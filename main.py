"""

Usage: memfog add
       memfog remove [--top <n> <keyword>...]
       memfog import [--force] <filepath>
       memfog export [<dirpath>]
       memfog [--top <n> --raw <keyword>...]

Options:
  -f --force    Overwrite existing records with imported records if same title
  -h --help     Show this screen
  -t --top <n>  Limit results to top n records [default: 10]
  -v --version  Show version

"""
#   -r --raw      Display raw links in record rather than content being linked to
from docopt import docopt
from fuzzywuzzy import fuzz
import multiprocessing
from more_itertools import unique_everseen
import datetime
import os
import time

from src import file_io, file_sys, ui, user, util
from src.record import Record, RecordGroup
from src.database import Database
from src.proxy import Flags

config = None


class ProcessHandler(multiprocessing.Process):
    """ Consumer that handles processing messages put in queue by UI """
    def __init__(self, q):
        super(ProcessHandler, self).__init__()
        self.daemon = True
        self.db = Database(config.db_fp)
        self.q = q

    def get_db_stream(self):
        return self.db.session.query(Record)

    def run(self):
        while True:
            context = self.q.get()

            switch = {
                Flags.INSERTRECORD : self.db.insert,
                Flags.UPDATERECORD : self.db.update,
                Flags.DELETERECORD : self.db.delete
            }

            switch[context.flag](context)

            # if context.flag == Flags.INSERTRECORD:
            #     self.db.insert(context)
            #
            # elif context.flag == Flags.UPDATERECORD:
            #     self.db.update(context)
            #
            # elif context.flag == Flags.DELETERECORD:
            #     self.db.delete(context)

            # Notify UI process that context has been fully processed and it can resume execution
            self.q.task_done()

class QContext:
    """ Message passed between producer (UI) and consumer (ProcessHandler) using queue """
    def __init__(self, record, interaction_mode, view_mode, flag):
        self.record = record
        self.interaction_mode = interaction_mode
        self.view_mode = view_mode
        self.flag = flag
        self.altered_fields = set()

class Memfog:
    def __init__(self):
        self.q = multiprocessing.JoinableQueue()
        ph = ProcessHandler(self.q)
        self.record_group = RecordGroup(ph.get_db_stream())
        ph.start()

    def create_rec(self):
        context = QContext(Record(), 'INSERT', 'RAW', Flags.INSERTRECORD)
        ui.UI(context, self.q)

    def display_rec(self, user_keywords):
        while True:
            try:
                Rec_fuzz_matches = self._fuzzy_match(user_keywords)
                record = self.display_rec_list(Rec_fuzz_matches, 'Display')
            except KeyboardInterrupt:
                break

            if record is not None:
                context = QContext(record, 'COMMAND', 'INTERPRETED', Flags.UPDATERECORD)
                ui.UI(context, self.q)
            else:
                break

    def display_rec_list(self, Rec_fuzz_matches, action_description):
        if len(self.record_group) > 0:
            print('{} which record?'.format(action_description))

            for i,Rec in enumerate(Rec_fuzz_matches):
                print('{}) [{}%] {}'.format(i, Rec.search_score, Rec.title))

            selection = user.get_input()

            if selection is not None:
                if selection < len(self.record_group):
                    return Rec_fuzz_matches[selection]
                else:
                    print('Invalid record selection \'{}\''.format(selection))
        else:
            print('No records exist')

    def export_recs(self, export_path):
        date = datetime.datetime.now()
        default_filename = 'memfog_{}-{}-{}.json'.format(date.month, date.day, date.year)
        target_path = os.getcwd() + '/' + default_filename

        if export_path is None:
            export_path = target_path

        # check if path to file pending export has been included in export_path
        if file_sys.check_path('w', export_path):
            target_path = export_path
        # check if path to directory to export into has been included in export_path
        else:
            if not export_path.endswith('/'):
                export_path += '/'
            if file_sys.check_path('w', export_path, default_filename):
                target_path = export_path + default_filename

        if os.path.exists(target_path):
            if not user.prompt_yn('Overwrite existing file {}'.format(target_path)):
                return

        rec_backups = [ Rec.dump() for Rec in self.record_group ]
        file_io.json_to_file(target_path, rec_backups)
        print('Exported to ' + target_path)

    def _fuzzy_match(self, user_input):
        user_keywords = ''.join(unique_everseen(util.standardize(user_input)))

        for record in self.record_group:
            keywords = ' '.join(record.make_set())
            record.search_score = (fuzz.token_sort_ratio(keywords, user_keywords) + fuzz.token_set_ratio(keywords, user_keywords)) / 2

        return [*sorted(self.record_group)][-config.top_n::]

    def import_recs(self, fp):
        imported_records = file_io.json_from_file(fp)
        skipped_imports = 0
        new_records = []

        for kwargs in imported_records:
            if kwargs['title'] not in self.record_group or config.force_import:
                new_records.append(Record(**kwargs))
            else:
                skipped_imports += 1
                print('Skipping duplicate - {}'.format(kwargs['title']))

        if len(new_records) > 0:
            ##### process should be only one accessing db
            self.db.bulk_insert(new_records)

        if skipped_imports > 0:
            print('Imported {}, Skipped {}'.format(len(imported_records) - skipped_imports, skipped_imports))
        else:
            print('Imported {}'.format(len(imported_records) - skipped_imports))

    def remove_rec(self, user_input):
        while True:
            Rec_fuzz_matches = self._fuzzy_match(user_input)
            record = self.display_rec_list(Rec_fuzz_matches, 'Remove')

            if record is not None and user.prompt_yn('Delete {}'.format(record.title)):
                context = QContext(record, '','', Flags.DELETERECORD)
                self.q.put(context)
                #self.ph.dh.db.remove(record)
                del self.record_group[record.title]
                Rec_fuzz_matches.remove(record)
            else:
                break

class Config:
    def __init__(self, argv):
        self.repo_dp = os.path.dirname(os.path.realpath(__file__))
        self.datadir_fp = self.repo_dp + '/datadir'
        self.db_fp = self.datadir_fp + '/memories.db'

        file_sys.init_dir(self.datadir_fp)

        self.force_import = argv['--force']
        self.top_n = argv['--top']
        #self.raw_links = argv['--raw']

        if self.top_n:
            if util.is_valid_input(self.top_n):
                self.top_n = int(self.top_n)
            else:
                print('Invalid list size entry \'{}\''.format(self.top_n))
                exit()

def main(argv):
    memfog = Memfog()

    user_input = ' '.join(argv['<keyword>'])

    if argv['add']:
        memfog.create_rec()
    elif argv['remove']:
        memfog.remove_rec(user_input)
    elif argv['export']:
        memfog.export_recs(argv['<dirpath>'])
    elif argv['import']:
        memfog.import_recs(argv['<filepath>'])
    elif len(memfog.record_group) > 0:
        memfog.display_rec(user_input)
    else:
        print('No memories exist')

if __name__ == '__main__':
    cli_args = docopt(__doc__, version='memfog v1.6.3')
    config = Config(cli_args)
    main(cli_args)

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
import threading
import queue
from more_itertools import unique_everseen
import datetime
import os

from src import file_io, file_sys, ui, user, util, database, record
from src.proxy import Flags

config = None


class DataHandler:
    def __init__(self):
        self.db = database.Database(config.db_fp)
        self.recs = record.RecordGroup(self.db.session.query(record.Record))

class QHandler:
    def __init__(self):
        self.dh = DataHandler()
        self.recv_queue = queue.Queue()
        self.send_queue = queue.Queue()
        # FIXME long delay occurs before ui loads, but it does load correctly and is functional
        #   however when trying to quit, it freezes and does not exit
        #   Tried changing from multiprocess to threading but same dely occurs
        #   Tried passing in queue's separately instead of Qhandler instances but same thing happened

    def listen(self):
        while True:
            flag, *args = self.recv_queue.get()
            print(flag, *args, '000000000000000000000000000000000000000')

            switch = {
                Flags.INSERTRECORD : self.dh.db.insert,
                Flags.UPDATERECORD : self.dh.db.update
            }

            switch[flag](*args)

class Memfog:
    def __init__(self):
        self.dh = DataHandler()
        self.qh = QHandler()

        t = threading.Thread(target=self.qh.listen)
        t.daemon = True
        t.start()

        self.excluded_words = file_io.set_from_file(config.exclusions_fp)

    def create_rec(self):
        rec = record.Record()
        self.qh.send_queue.put(Flags.INSERTRECORD)
        Gui = ui.UI(self.qh.send_queue, self.qh.recv_queue, rec, 'INSERT')

        # if Gui.db_update_required:
        #     [setattr(rec, k, v) for k,v in Gui.Data.raw_view.dump().items()]
        #     self.DB.insert(rec)

    def display_rec(self, user_keywords):
        while True:
            try:
                Rec_fuzz_matches = self._fuzzy_match(user_keywords)
                rec = self.display_rec_list(Rec_fuzz_matches, 'Display')
            except KeyboardInterrupt:
                break

            if rec is not None:
                # if not self.config.raw_links:
                #     Rec.body = link.expand(Rec.body)

                self.qh.send_queue.put(Flags.UPDATERECORD)
                Gui = ui.UI(self.qh.send_queue, self.qh.recv_queue, rec)

                # if Gui.db_update_required:
                #     updated_keys = util.k_intersect_v_diff(Rec.dump(), Gui.Data.raw_view.dump())
                #     [setattr(Rec, k, getattr(Gui.Data.raw_view, k)) for k in updated_keys]
                #     self.DB.update(Rec, updated_keys)
            else:
                break

    def display_rec_list(self, Rec_fuzz_matches, action_description):
        if len(self.dh.recs) > 0:
            print('{} which record?'.format(action_description))

            for i,Rec in enumerate(Rec_fuzz_matches):
                print('{}) [{}%] {}'.format(i, Rec.search_score, Rec.title))

            selection = user.get_input()

            if selection is not None:
                if selection < len(self.dh.recs):
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

        rec_backups = [ Rec.dump() for Rec in self.dh.recs ]
        file_io.json_to_file(target_path, rec_backups)
        print('Exported to ' + target_path)

    def _fuzzy_match(self, user_input):
        user_keywords = ''.join(unique_everseen(util.standardize(user_input)))

        for rec in self.dh.recs:
            keyword_set = rec.make_set()
            keyword_set.difference_update(self.excluded_words)
            keywords = ' '.join(keyword_set)
            score = (fuzz.token_sort_ratio(keywords, user_keywords) + fuzz.token_set_ratio(keywords, user_keywords)) / 2
            rec.search_score = score

        return [*sorted(self.dh.recs)][-config.top_n::]

    def import_recs(self, fp):
        imported_records = file_io.json_from_file(fp)
        skipped_imports = 0
        new_records = []

        for rec in imported_records:
            if rec['title'] not in self.dh.recs or config.force_import:
                new_records.append(rec.Record(**rec))
            else:
                skipped_imports += 1
                print('Skipping duplicate - {}'.format(rec['title']))

        if len(new_records) > 0:
            self.dh.db.bulk_insert(new_records)

        if skipped_imports > 0:
            print('Imported {}, Skipped {}'.format(len(imported_records) - skipped_imports, skipped_imports))
        else:
            print('Imported {}'.format(len(imported_records) - skipped_imports))

    def remove_rec(self, user_input):
        while True:
            Rec_fuzz_matches = self._fuzzy_match(user_input)
            recs = self.display_rec_list(Rec_fuzz_matches, 'Remove')

            if recs and user.prompt_yn('Delete {}'.format(recs.title)):
                self.dh.db.remove(recs)
                del self.dh.recs[recs.title]
                Rec_fuzz_matches.remove(recs)
            else:
                break

class Config:
    def __init__(self, argv):
        self.repo_dp = os.path.dirname(os.path.realpath(__file__))
        self.datadir_fp = self.repo_dp + '/datadir'
        self.db_fp = self.datadir_fp + '/memories.db'
        self.exclusions_fp = self.datadir_fp + '/exclusions.txt'

        file_sys.init_dir(self.datadir_fp)
        file_sys.init_file(self.exclusions_fp)

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
    elif len(memfog.dh.recs) > 0:
        memfog.display_rec(user_input)
    else:
        print('No memories exist')

if __name__ == '__main__':
    cli_args = docopt(__doc__, version='memfog v1.6.2.3')
    config = Config(cli_args)
    main(cli_args)

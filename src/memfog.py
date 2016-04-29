from fuzzywuzzy import fuzz
import multiprocessing
import datetime
import os

from . import file_io, file_sys, ui, user, util
from .record import Record, RecordGroup
from .database import Database
from .proxy import Flags


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
                Flags.DELETERECORD : self.db.delete,
                Flags.BULKINSERTRECORD : self.db.bulk_insert
            }

            switch[context.flag](context)

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
                Rec_fuzz_matches = self.fuzzy_match(user_keywords)
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

    def fuzzy_match(self, user_input):
        user_keywords = ''.join(util.unique_everseen(util.standardize(user_input)))

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
            context = QContext(new_records, '', '', Flags.BULKINSERTRECORD)
            self.q.put(context)
            self.q.join()

        if skipped_imports > 0:
            print('Imported {}, Skipped {}'.format(len(imported_records) - skipped_imports, skipped_imports))
        else:
            print('Imported {}'.format(len(imported_records) - skipped_imports))

    def remove_rec(self, user_input):
        while True:
            Rec_fuzz_matches = self.fuzzy_match(user_input)
            record = self.display_rec_list(Rec_fuzz_matches, 'Remove')

            if record is not None and user.prompt_yn('Delete {}'.format(record.title)):
                context = QContext(record, '','', Flags.DELETERECORD)
                self.q.put(context)
                self.q.join()
                del self.record_group[record.title]
                Rec_fuzz_matches.remove(record)
            else:
                break

from fuzzywuzzy import fuzz
import multiprocessing
import datetime
from pathlib import Path

from . import file_io, ui, user, util
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
            try:
                context = self.q.get()
            except KeyboardInterrupt:
                break

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
    def __init__(self, record, flag, i_mode='', v_mode=''):
        self.record = record
        self.interaction_mode = i_mode
        self.view_mode = v_mode
        self.flag = flag
        self.altered_fields = set()


class Memfog:
    def __init__(self):
        self.q = multiprocessing.JoinableQueue()
        ph = ProcessHandler(self.q)
        self.record_group = RecordGroup(ph.get_db_stream())
        ph.start()

    def create_rec(self):
        context = QContext(Record(), Flags.INSERTRECORD, i_mode='INSERT', v_mode='RAW')
        ui.UI(context, self.q)

    def display_rec(self, user_keywords):
        Rec_fuzz_matches = self.fuzzy_match(user_keywords)
        record = self.display_rec_list(Rec_fuzz_matches, 'Display')

        if record is not None:
            context = QContext(record, Flags.UPDATERECORD, i_mode='COMMAND', v_mode='INTERPRETED')
            ui.UI(context, self.q)

    def display_rec_list(self, Rec_fuzz_matches, action_description):
        if len(self.record_group) > 0:
            print('{} which record?'.format(action_description))

            for i,Rec in enumerate(Rec_fuzz_matches):
                print('{}) [{}%] {}'.format(i, Rec.search_score, Rec.title))

            try:
                selection = user.get_input()
            except KeyboardInterrupt:
                return

            if selection is not None:
                if selection < len(self.record_group):
                    return Rec_fuzz_matches[selection]
                else:
                    print('Invalid record selection \'{}\''.format(selection))
        else:
            print('No records exist')

    def export_recs(self, target_path):
        date = datetime.datetime.now()
        default_fn = 'memfog_{}-{}-{}.json'.format(date.month, date.day, date.year)

        if target_path is None:
            target_path = config.project_dp / default_fn
        else:
            target_path = Path(target_path).expanduser()

        if target_path.is_dir():
            target_path = target_path / default_fn

        if target_path.exists():
            if not user.prompt_yn('Overwrite existing file {}'.format(target_path)):
                return

        rec_backups = [ Rec.dump() for Rec in self.record_group ]
        file_io.json_to_file(target_path, rec_backups)
        print('Exported to ' + str(target_path))

    def fuzzy_match(self, user_input):
        user_keywords = ' '.join(util.unique_everseen(util.standardize(user_input)))
        for record in self.record_group:
            keywords = ' '.join(record.make_set())
            record.search_score = fuzz.token_sort_ratio(keywords, user_keywords)
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
            context = QContext(new_records, flag=Flags.BULKINSERTRECORD)
            self.q.put(context)
            self.q.join()

        if skipped_imports > 0:
            print('Imported {}, Skipped {}'.format(len(imported_records) - skipped_imports, skipped_imports))
        else:
            print('Imported {}'.format(len(imported_records) - skipped_imports))

    def remove_rec(self, user_input):
        Rec_fuzz_matches = self.fuzzy_match(user_input)
        record = self.display_rec_list(Rec_fuzz_matches, 'Remove')

        if record is not None and user.prompt_yn('Delete {}'.format(record.title)):
            context = QContext(record, flag=Flags.DELETERECORD)
            self.q.put(context)
            self.q.join()
            del self.record_group[record.title]
            Rec_fuzz_matches.remove(record)


"""

Usage: memfog add
       memfog remove [--top <n> <keyword>...]
       memfog import [--force] <filepath>
       memfog export [<dirpath>]
       memfog [--top <n> <keyword>...]

Options:
  -h --help     Show this screen
  -v --version  Show version
  -t --top <n>  Limit results to top n records [default: 10]
  -f --force    Overwrite existing records with imported records if same title

"""
from docopt import docopt
from fuzzywuzzy import fuzz
import datetime
import os

from src import fs, io, ui, user, util
from src.db import Database, Record

class Memfog:
    def __init__(self, config):
        self.config = config
        self.excluded_words = io.set_from_file(self.config.exclusions_fp)
        self.db = Database(self.config.db_fp)
        self.records = { Rec.title:Rec for Rec in self.db.session.query(Record).all() }

    def export_recs(self, export_dp):
        """
        :type export_dp: str
        """
        if export_dp is None or not os.path.exists(export_dp):
            export_dp = os.getcwd()

        date = datetime.datetime.now()
        export_dp = fs.validate_dir_path(export_dp, os.getcwd())
        export_fp = export_dp + 'memfog_{}-{}-{}.json'.format(date.month, date.day, date.year)

        if os.path.isfile(export_fp):
            if not user.prompt_yn('Overwrite existing file {}'.format(export_fp)):
                return

        rec_backups = [ Rec.dump() for Rec in self.records.values() ]
        io.json_to_file(export_fp, rec_backups)

    def create_rec(self):
        Rec = Record()

        # construct Record from data entered into UI
        Gui = ui.UI(Rec)

        if Gui.altered:
            [setattr(Rec, k, v) for k,v in Gui.dump().items()]
            self.db.insert(Rec)

    def display_rec(self, user_keywords):
        """
        :type user_keywords: str
        """
        # TODO if memory is selected and title is changed, match % should update when returning to Record list
        Rec_fuzz_matches = self._fuzzy_match(user_keywords)
        while True:
            try:
                Rec = self.display_rec_list(Rec_fuzz_matches, 'Display')
            except KeyboardInterrupt:
                break

            # Rec is None when user enters an invalid record selection or hits ENTER with no selection
            if Rec is not None:
                Gui = ui.UI(Rec)

                if Gui.altered:
                    updated_keys = util.differing_keys(Rec.dump(), Gui.dump())
                    [setattr(Rec, k, getattr(Gui, k)) for k in updated_keys]
                    self.db.update(Rec, updated_keys)
            else:
                break

    def import_recs(self, fp):
        """
        :type fp: str
        """
        imported_records = io.json_from_file(fp)
        skipped_imports = 0
        new_records = []

        for record in imported_records:
            if record['title'] not in self.records or self.config.force_import:
                new_records.append(Record(**record))
            else:
                skipped_imports += 1
                print('Skipping duplicate - {}'.format(record['title']))

        if len(new_records) > 0:
            self.db.bulk_insert(new_records)

        if skipped_imports > 0:
            print('Imported {}, Skipped {}'.format(len(imported_records) - skipped_imports, skipped_imports))
        else:
            print('Imported {}'.format(len(imported_records) - skipped_imports))

    def _fuzzy_match(self, user_input):
        """
        :type user_input: str
        :returns: top_n Records from self.records sorted by Record.search_score in ascending order
        """
        user_search_str = ''.join(set(util.standardize(user_input)))

        for Rec in self.records.values():
            word_set = Rec.make_set()
            word_set.difference_update(self.excluded_words)
            word_str = ' '.join(word_set)
            Rec.search_score = fuzz.token_set_ratio(word_str, user_search_str)

        return [*sorted(self.records.values())][-self.config.top_n::]

    def remove_rec(self, user_input):
        """
        :type user_input: str
        """
        while True:
            Rec_fuzz_matches = self._fuzzy_match(user_input)
            Rec = self.display_rec_list(Rec_fuzz_matches, 'Remove')

            if Rec and user.prompt_yn('Delete {}'.format(Rec.title)):
                self.db.remove(Rec)
                del self.records[Rec.title]
                Rec_fuzz_matches.remove(Rec)
            else:
                break

    def display_rec_list(self, Rec_fuzz_matches, action_description):
        """
        :type Rec_fuzz_matches: list of Record objects
        :type action_description: str
        :returns: Record object or None
        """
        if len(self.records) > 0:
            print('{} which record?'.format(action_description))

            for i,Rec in enumerate(Rec_fuzz_matches):
                print('{}) [{}%] {}'.format(i, Rec.search_score, Rec.title))

            selection = user.get_input()

            if selection is not None:
                if selection < len(self.records):
                    return Rec_fuzz_matches[selection]
                else:
                    print('Invalid record selection \'{}\''.format(selection))
        else:
            print('No records exist')

class Config:
    def __init__(self, argv):
        self.data_dir = 'datadir/'
        self.db_name = 'memories.db'
        self.exclusions_fp = 'exclusions.txt'

        self.repo_dp = os.path.dirname(os.path.realpath(__file__))
        self.datadir_fp = self.repo_dp + '/' + self.data_dir
        self.db_fp = self.datadir_fp + self.db_name
        self.exclusions_fp = self.datadir_fp + self.exclusions_fp

        fs.init_dir(self.datadir_fp)
        fs.init_file(self.exclusions_fp)

        self.force_import = argv['--force']

        top_n = argv['--top']
        if top_n:
            if util.is_valid_input(top_n): self.top_n = int(top_n)
            else: print('Invalid list size entry \'{}\''.format(top_n))

def main(argv):
    Conf = Config(argv)
    memfog = Memfog(Conf)

    # delimit words with whitespace so they can be processed at same time as memory string data
    user_input = ' '.join(argv['<keyword>'])

    if argv['add']:
        memfog.create_rec()
    elif argv['remove']:
        memfog.remove_rec(user_input)
    elif argv['export']:
        memfog.export_recs(argv['<dir_path>'])
    elif argv['import']:
        memfog.import_recs(argv['<file_path>'])
    elif len(memfog.records) > 0:
        memfog.display_rec(user_input)
    else:
        print('No memories exist')

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.5.0')
    main(args)

"""

Usage: memfog add
       memfog remove [--top <n> <keyword>...]
       memfog import [--force] <filepath>
       memfog export [<dirpath>]
       memfog [--top <n> --raw <keyword>...]

Options:
  -f --force    Overwrite existing records with imported records if same title
  -h --help     Show this screen
  -r --raw      Display raw links in record rather than content being linked to
  -t --top <n>  Limit results to top n records [default: 10]
  -v --version  Show version

"""
from docopt import docopt
from fuzzywuzzy import fuzz
from more_itertools import unique_everseen
import datetime
import os

from src import file_io, file_sys, link, ui, user, util
from src.db import Database, Record

class Memfog:
    def __init__(self, config):
        self.config = config
        self.excluded_words = file_io.set_from_file(self.config.exclusions_fp)
        self.DB = Database(self.config.db_fp)
        self.Records = { Rec.title:Rec for Rec in self.DB.session.query(Record).all() }
        self.RecLink = link.Link()

    def create_rec(self):
        Rec = Record()

        # construct Record from data entered into UI. Start UI in INSERT mode since a new record is being created
        Gui = ui.UI(Rec, 'INSERT')

        if Gui.altered():
            [setattr(Rec, k, v) for k,v in Gui.dump().items()]
            self.DB.insert(Rec)

    def display_rec(self, user_keywords):
        """
        :type user_keywords: str
        """
        while True:
            try:
                Rec_fuzz_matches = self._fuzzy_match(user_keywords)
                Rec = self.display_rec_list(Rec_fuzz_matches, 'Display')
            except KeyboardInterrupt:
                break

            # Rec is None when user enters an invalid record selection or hits ENTER with no selection
            if Rec is not None:
                if not self.config.raw_links:
                    Rec.body = self.RecLink.expand(Rec.body)

                Gui = ui.UI(Rec)

                if Gui.altered():
                    updated_keys = util.k_intersect_v_diff(Rec.dump(), Gui.dump())
                    [setattr(Rec, k, getattr(Gui, k)) for k in updated_keys]
                    self.DB.update(Rec, updated_keys)
            else:
                break

    def display_rec_list(self, Rec_fuzz_matches, action_description):
        """
        :type Rec_fuzz_matches: list of Record objects
        :type action_description: str
        :returns: Record object or None
        """
        if len(self.Records) > 0:
            print('{} which record?'.format(action_description))

            for i,Rec in enumerate(Rec_fuzz_matches):
                print('{}) [{}%] {}'.format(i, Rec.search_score, Rec.title))

            selection = user.get_input()

            if selection is not None:
                if selection < len(self.Records):
                    return Rec_fuzz_matches[selection]
                else:
                    print('Invalid record selection \'{}\''.format(selection))
        else:
            print('No records exist')

    def export_recs(self, export_dp):
        """
        :type export_dp: str
        """
        if export_dp is None or not os.path.exists(export_dp):
            export_dp = os.getcwd()

        date = datetime.datetime.now()
        export_dp = file_sys.validate_dir_path(export_dp, os.getcwd())
        export_fp = export_dp + 'memfog_{}-{}-{}.json'.format(date.month, date.day, date.year)

        if os.path.isfile(export_fp):
            if not user.prompt_yn('Overwrite existing file {}'.format(export_fp)):
                return

        rec_backups = [ Rec.dump() for Rec in self.Records.values() ]
        file_io.json_to_file(export_fp, rec_backups)

    def _fuzzy_match(self, user_input):
        """
        :type user_input: str
        :returns: top_n Records from self.records sorted by Record.search_score in ascending order
        """
        user_search_str = ''.join(unique_everseen(util.standardize(user_input)))

        for Rec in self.Records.values():
            word_set = Rec.make_set()
            word_set.difference_update(self.excluded_words)
            word_str = ' '.join(word_set)
            Rec.search_score = fuzz.token_set_ratio(word_str, user_search_str)

        return [*sorted(self.Records.values())][-self.config.top_n::]

    def import_recs(self, fp):
        """
        :type fp: str
        """
        imported_records = file_io.json_from_file(fp)
        skipped_imports = 0
        new_records = []

        for record in imported_records:
            if record['title'] not in self.Records or self.config.force_import:
                new_records.append(Record(**record))
            else:
                skipped_imports += 1
                print('Skipping duplicate - {}'.format(record['title']))

        if len(new_records) > 0:
            self.DB.bulk_insert(new_records)

        if skipped_imports > 0:
            print('Imported {}, Skipped {}'.format(len(imported_records) - skipped_imports, skipped_imports))
        else:
            print('Imported {}'.format(len(imported_records) - skipped_imports))

    def remove_rec(self, user_input):
        """
        :type user_input: str
        """
        while True:
            Rec_fuzz_matches = self._fuzzy_match(user_input)
            Rec = self.display_rec_list(Rec_fuzz_matches, 'Remove')

            if Rec and user.prompt_yn('Delete {}'.format(Rec.title)):
                self.DB.remove(Rec)
                del self.Records[Rec.title]
                Rec_fuzz_matches.remove(Rec)
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
        self.raw_links = argv['--raw']

        if self.top_n:
            if util.is_valid_input(self.top_n):
                self.top_n = int(self.top_n)
            else:
                print('Invalid list size entry \'{}\''.format(self.top_n))
                exit()

def main(argv):
    Conf = Config(argv)
    memfog = Memfog(Conf)

    user_input = ' '.join(argv['<keyword>'])

    if argv['add']:
        memfog.create_rec()
    elif argv['remove']:
        memfog.remove_rec(user_input)
    elif argv['export']:
        memfog.export_recs(argv['<dirpath>'])
    elif argv['import']:
        memfog.import_recs(argv['<filepath>'])
    elif len(memfog.Records) > 0:
        memfog.display_rec(user_input)
    else:
        print('No memories exist')

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.6.1')
    main(args)

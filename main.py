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
from more_itertools import unique_everseen
import datetime
import os

from src import file_io, file_sys, instruction, ui, user, util
from src.db import Database, Record

class Memfog:
    def __init__(self, config):
        self.config = config
        self.excluded_words = file_io.set_from_file(self.config.exclusions_fp)
        self.DB = Database(self.config.db_fp)
        self.Records = { Rec.title:Rec for Rec in self.DB.session.query(Record).all() }

    def create_rec(self):
        """ Initializes a new Record object which is passed to the command line interface. The empty Record's
        data members are then be set according to the user's text input """
        Rec = Record()

        # construct Record from data entered into UI. Start UI in INSERT mode since a new record is being created
        Gui = ui.UI(Rec, 'INSERT')

        if Gui.db_update_required:
            [setattr(Rec, k, v) for k,v in Gui.Data.raw_view.dump().items()]
            self.DB.insert(Rec)

    def display_rec(self, user_keywords):
        """
        :type user_keywords: str
        Initializes command line interface with user selected Record. Data members in Record are used to
        populate the UI widget fields with text prior to displaying them on screen
        """
        while True:
            try:
                Rec_fuzz_matches = self._fuzzy_match(user_keywords)
                Rec = self.display_rec_list(Rec_fuzz_matches, 'Display')
            except KeyboardInterrupt:
                break

            # Rec is None when user enters an invalid record selection or hits ENTER with no selection
            if Rec is not None:
                # if not self.config.raw_links:
                #     Rec.body = link.expand(Rec.body)

                Gui = ui.UI(Rec)

                if Gui.db_update_required:
                    updated_keys = util.k_intersect_v_diff(Rec.dump(), Gui.Data.raw_view.dump())
                    [setattr(Rec, k, getattr(Gui.Data.raw_view, k)) for k in updated_keys]
                    self.DB.update(Rec, updated_keys)
            else:
                break

    def display_rec_list(self, Rec_fuzz_matches, action_description):
        """
        :type Rec_fuzz_matches: list of Record objects
        :type action_description: str
        :returns: Record object or None
        Prints record titles in descending order by their match percentage to the users keyword input
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

    def export_recs(self, export_path):
        """
        :type export_path: str
        Exports a json file of all records in database to directory at path dp
        """
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

        rec_backups = [ Rec.dump() for Rec in self.Records.values() ]
        file_io.json_to_file(target_path, rec_backups)
        print('Exported to ' + target_path)

    def _fuzzy_match(self, user_input):
        """
        :type user_input: str
        :returns: top_n Records from self.records sorted by Record.search_score in ascending order
        Takes a set of string for each record from the header and keywords and uses the set to
        perform fuzzy string matching to calculate match percentage to the user_input keywords
        """
        user_keywords = ''.join(unique_everseen(util.standardize(user_input)))

        for Rec in self.Records.values():
            keyword_set = Rec.make_set()
            keyword_set.difference_update(self.excluded_words)
            keywords = ' '.join(keyword_set)
            score = (fuzz.token_sort_ratio(keywords, user_keywords) + fuzz.token_set_ratio(keywords, user_keywords)) / 2
            Rec.search_score = score

        return [*sorted(self.Records.values())][-self.config.top_n::]

    def import_recs(self, fp):
        """
        :type fp: str
        Imports record from a json file located at fp by individually inserting them into the database
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
        Displays records matching user input and removes the selected record from database
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
    """ Contains application configuration settings """
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
    args = docopt(__doc__, version='memfog v1.6.2.3')
    main(args)

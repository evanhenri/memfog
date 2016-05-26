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
import pkg_resources
from docopt import docopt
import sys
import os

from . import memfog as mf
from . import file_sys
from .file_sys import Path
from . import util


class Config:
    def __init__(self, argv):
        self.home_dp = os.path.expanduser('~')
        self.project_dp = Path(self.home_dp, 'memfog')
        self.data_dp = Path(self.project_dp, 'data')
        self.db_fp = Path(self.data_dp, 'records.db')

        file_sys.init_dir(self.project_dp)
        file_sys.init_dir(self.data_dp)

        self.force_import = argv['--force']
        self.top_n = argv['--top']

        if self.top_n:
            if util.is_valid_input(self.top_n):
                self.top_n = int(self.top_n)
            else:
                sys.exit('Invalid list size entry \'{}\''.format(self.top_n))


def main():
    argv = docopt(__doc__, version=pkg_resources.require('memfog')[0].version)

    mf.config = Config(argv)
    memfog = mf.Memfog()

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
    main()

"""

Usage: memfog [--add]
       memfog [--remove <keyword>...] [--top <n>]
       memfog [--export <dir_path>]
       memfog [(--import <file_path>)]

Options:
  -h --help     Show this screen
  -v --version  Show version
  -a --add      Create new memory record
  -r --remove   List records containing keywords and remove selected
  -t --top <n>  Limit results to top n memories [default: 10]
  -e --export   Export memory records to json file
  -i --import   Load memories from json file

"""
from docopt import docopt
import os

from src import fs, data, brain

class Config:
    def __init__(self, root_dir):
        self.top_n = 10
        self.data_dir = 'datadir/'
        self.mem_db = 'memories.db'
        self.body_dir = 'body/'
        self.exclusions_file = 'exclusions.txt'

        self.data_dir_path = root_dir + self.data_dir
        self.mem_db_path = self.data_dir_path + self.mem_db
        self.body_dir_path = self.data_dir_path + self.body_dir
        self.exclusions_file_path = self.data_dir_path + self.exclusions_file

        fs.init_dir(self.data_dir_path)
        fs.init_dir(self.body_dir_path)
        fs.init_file(self.exclusions_file_path)

def main(argv):
    root_dir = os.path.dirname(os.path.realpath(__file__)) + '/'
    Conf = Config(root_dir)

    top_n = argv['--top']
    if top_n:
        if data.is_valid_input(top_n): Conf.top_n = int(top_n)
        else: print('Invalid threshold value \'{}\''.format(top_n))

    Brain = brain.Brain(Conf)

    # delimit words with whitespace so they can be processed at same time as memory string data
    user_input = ' '.join(argv['<keyword>'])

    if argv['--add']:
        Brain.create_mem()
    elif argv['--remove']:
        Brain.remove_mem(user_input)
    elif argv['--export']:
        Brain.export_mem(argv['<dir_path>'])
    elif argv['--import']:
        Brain.import_mem(argv['<file_path>'])
    elif len(Brain.memories) > 0:
        Brain.display_mem(user_input)
    else:
        print('No memories exist')

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.4.0')
    main(args)

"""
Usage: memfog add
       memfog remove [--top <n> <keyword>...]
       memfog import [--force] <file_path>
       memfog export [<dir_path>]
       memfog [--top <n> <keyword>...]

Options:
  -h --help     Show this screen
  -v --version  Show version
  -t --top <n>  Limit results to top n memories [default: 10]
  -f --force    Overwrite existing memories with imported memories if same title

"""
from docopt import docopt
import os

from src import fs, data, brain

class Config:
    def __init__(self, root_dir):
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

        self.top_n = 10
        self.force_import = False

def main(argv):
    root_dir = os.path.dirname(os.path.realpath(__file__)) + '/'
    Conf = Config(root_dir)

    Conf.force_import = argv['--force']
    top_n = argv['--top']
    if top_n:
        if data.is_valid_input(top_n): Conf.top_n = int(top_n)
        else: print('Invalid threshold value \'{}\''.format(top_n))

    Brain = brain.Brain(Conf)

    # delimit words with whitespace so they can be processed at same time as memory string data
    user_input = ' '.join(argv['<keyword>'])

    if argv['add']:
        Brain.create_mem()
    elif argv['remove']:
        Brain.remove_mem(user_input)
    elif argv['export']:
        Brain.export_mem(argv['<dir_path>'])
    elif argv['import']:
        Brain.import_mem(argv['<file_path>'])
    elif len(Brain.memories) > 0:
        Brain.display_mem(user_input)
    else:
        print('No memories exist')

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.4.0')
    main(args)

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

from src import data, brain

def main(argv):
    Brain = brain.Brain()

    top_n = argv['--top']
    if top_n:
        if data.is_valid_input(top_n):
            Brain.top_n = int(top_n)
        else:
            print('Invalid threshold value \'{}\''.format(top_n))

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

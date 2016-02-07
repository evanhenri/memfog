"""

Usage: memfog [--add|--remove|--edit] [<keyword>...] [--top <n>]
       memfog [--backup <dir_path>]
       memfog [(--import <file_path>)]

Options:
  -h --help     Show this screen
  -v --version  Show version
  -a --add      Create new memory record
  -r --remove   List records containing keywords and remove selected
  -e --edit     List records containing keywords and edit details of selected
  -t --top <n>  Limit results to top n memories [default: 10]
  -b --backup   Backup memory records to json file
  -i --import   Load memories from json file

"""
import os
from docopt import docopt

from src import io, data, brain

def main(argv):
    root_path = os.path.dirname(os.path.realpath(__file__))
    brain_file = '{}/brain.pkl'.format(root_path)
    brain_obj = io.pkl_from_file(brain_file)

    if not brain_obj:
        brain_obj = brain.Brain()
        brain_obj.altered = True

    top_n = argv['--top']
    if top_n:
        if data.is_valid_input(top_n):
            brain_obj.top_n = int(top_n)
        else:
            print('Invalid threshold value \'{}\''.format(top_n))

    # delimit words with whitespace so they can be processed at same time as memory string data
    user_keywords = ' '.join(argv['<keyword>'])

    if argv['--add']:
        # assumed that keywords entered are the memory title for the new memory being added
        brain_obj.create_memory(user_keywords)
    elif argv['--remove']:
        brain_obj.remove_memory(user_keywords)
    elif argv['--edit']:
        brain_obj.edit_memory(user_keywords)
    elif argv['--backup']:
        brain_obj.backup_memories(argv['<dir_path>'])
    elif argv['--import']:
        brain_obj.import_memories(argv['<file_path>'])
    elif len(brain_obj.memories) > 0:
        brain_obj.display_memory(user_keywords)
    else:
        print('No memories exist')

    if brain_obj.altered:
        brain_obj.altered = False
        io.pkl_to_file(brain_file, brain_obj)

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.0.1')
    main(args)

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
    repo_root = os.path.dirname(os.path.realpath(__file__))
    mem_file = 'memories.db'
    mem_path = repo_root + '/' + mem_file
    exclusion_file = repo_root + '/src/excluded_words.txt'

    if not os.path.isfile(exclusion_file): io.mkfile(exclusion_file)

    Brain = brain.Brain(mem_path)
    Brain.excluded_words = io.set_from_file(exclusion_file)

    for m in Brain.memories:
        print(m)
    exit()

    top_n = argv['--top']
    if top_n:
        if data.is_valid_input(top_n):
            Brain.top_n = int(top_n)
        else:
            print('Invalid threshold value \'{}\''.format(top_n))

    # delimit words with whitespace so they can be processed at same time as memory string data
    user_keywords = ' '.join(argv['<keyword>'])

    if argv['--add']:
        # assumed that keywords entered are the memory title for the new memory being added
        Brain.create_memory(user_keywords)
    elif argv['--remove']:
        Brain.remove_memory(user_keywords)
    elif argv['--edit']:
        Brain.edit_memory(user_keywords)
    elif argv['--backup']:
        Brain.backup_memories(argv['<dir_path>'])
    elif argv['--import']:
        Brain.import_memories(argv['<file_path>'])
    elif len(Brain.memories) > 0:
        Brain.display_memory(user_keywords)
    else:
        print('No memories exist')

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.1.0')
    main(args)

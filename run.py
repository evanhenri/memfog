"""memfog
Usage:
  run.py [<keyword>...[--add | --rm | --edit]]

Options:
  -h --help     Show this screen
  -v --version  Show version
  -a --add      Create new memory record
  -r --rm       List records containing keywords and remove selected
  -e --edit     List records containing keywords and edit details of selected
"""
from docopt import docopt
import readline
import pickle
import string
import os

def valid_input(s):
    return len(s) > 0 and s.isdigit() and int(s) >= 0

def default_input(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)
   finally:
      readline.set_startup_hook()

def strip_whitespace(s):
    return ''.join([c for c in s if c not in string.whitespace])

def strip_punctuation(s):
    exclusions = ['\'','"']
    return ''.join([c for c in s if c not in string.punctuation or c in exclusions])

def standardize(s):
    stripped = strip_punctuation(s).lower()
    arr = stripped.split(' ')
    arr_no_ws = map(strip_whitespace, arr)
    return [w for w in arr_no_ws if len(w) > 0]

class Brain:
    def __init__(self):
        self.memory_ids = {0}
        self.brain_file = 'brain.pkl'
        self.memories = {}

    def create_memory(self):
        M = Memory()

        # require input for all memory variables
        M.update_title()
        M.update_keywords()
        M.update_body()

        self.memories.setdefault(self._get_memory_id(), M)

    def edit_memory(self, user_keywords):
        memory_matches = self._memory_match(user_keywords)
        m_id = self._select_memory_from_list(memory_matches)
        self.memories[m_id].edit_menu()
        print('Successfully edited \'{}\''.format(self.memories[m_id].title))

    def _get_memory_id(self):
        next_id = min(self.memory_ids)
        self.memory_ids.remove(next_id)

        #
        if len(self.memory_ids) == 0:
            self.memory_ids.add(next_id+1)

        print(next_id, self.memory_ids)
        return next_id

    def _memory_match(self, user_keywords):

        user_keywords = set(standardize(user_keywords))

        for memory in self.memories.values():
            memory_keywords = memory.make_set()
            memory.search_score = len(user_keywords.intersection(memory_keywords))

        # memories are sorted by search score
        matches = sorted(self.memories.items(), key=lambda x: x[1])

        # reset search score for all memories
        for m in self.memories.values():
            m.search_score=0

        return matches

    def recall_memory(self, user_keywords):
        memory_matches = self._memory_match(user_keywords)
        [print('{}\n\t{}'.format(m[1].title, m[1].body)) for m in memory_matches]

    def remove_memory(self, user_keywords):
        memory_matches = self._memory_match(user_keywords)
        m_id = self._select_memory_from_list(memory_matches)
        del self.memories[m_id]

    def _select_memory_from_list(self, memory_matches):
        [print('{}){}'.format(i, m.title)) for i,m in memory_matches]
        selection = input('> ')
        if valid_input(selection):
            selection = int(selection)
            if selection in self.memories:
                return selection
            else:
                print('Invalid memory id \'{}\''.format(selection))
        else:
            print('Invalid entry \'{}\''.format(selection))

class Memory:
    def __init__(self):
        self.title = ''
        self.keywords = ''
        self.body = ''
        self.search_score = 0
    def __gt__(self, other_memory):
        return self.search_score > other_memory.search_score

    def update_title(self):
        self.title = default_input('Title: ', self.title)
    def update_keywords(self):
        self.keywords = default_input('Keywords: ', self.keywords)
    def update_body(self):
        self.body = default_input('Body: ', self.body)
    def edit_menu(self):
        while True:
            print('0) Edit Title\n1) Edit Keywords\n2) Edit Body\n3) Done')
            selection = input('> ')

            if valid_input(selection):
                selection = int(selection)
                options = {
                    0:self.update_title,
                    1:self.update_keywords,
                    2:self.update_body,
                }

                if selection == 3:
                    if len(input('Press ENTER to Confirm')) == 0:
                        return
                else:
                    options[selection]()

    def make_set(self):
        memory_data = ' '.join([self.title, self.keywords, self.body])
        return set(standardize(memory_data))

def main(argv):
    # print(argv)

    brain_file = 'brain.pkl'
    brain = None

    ########################################### load
    try:
        with open(brain_file, 'rb') as in_stream:
            if os.path.getsize(brain_file) > 0:
                brain = pickle.load(in_stream)
    except FileNotFoundError:
        print('{} not found, creating new {} file'.format(brain_file, brain_file.split('.')[0]))
        brain = Brain()
    except Exception:
        print('Error occured while loading {}'.format(brain_file))
        exit()


    # delimit words with whitespace so they can be processed at same time as stored strings
    user_keywords = ' '.join(argv['<keyword>'])

    if argv['--add']:
        brain.create_memory()
    elif argv['--rm']:
        brain.remove_memory(user_keywords)
    elif argv['--edit']:
        brain.edit_memory(user_keywords)
    elif len(user_keywords) > 0:
        if len(brain.memories) > 0:
            brain.recall_memory(user_keywords)
        else:
            print('No memories exist')
    else:
        print('No keywords supplied')


    ########################################### save
    try:
        with open(brain_file, 'wb') as out_stream:
            pickle.dump(brain, out_stream, pickle.HIGHEST_PROTOCOL)
        print('Memory saved')
    except Exception:
        print('Error occured while saving {}'.format(brain_file))
        exit()

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.0.0')
    main(args)

"""
todo


"""

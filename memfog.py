"""memfog
Usage:
  memfog.py [<keyword>...] [--add | --remove | --edit]

Options:
  -h --help     Show this screen
  -v --version  Show version
  -a --add      Create new memory record
  -r --remove   List records containing keywords and remove selected
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
        self.memory_keys = {0}
        self.memories = {}
        self.altered = False

    def create_memory(self, user_title=None):
        m = Memory()

        # if user provided a title in program args, set memory title using their entry
        if user_title: m.title = user_title
        # otherwise prompt them for a title entry
        else: m.update_title()

        m.update_keywords()
        m.update_body()

        self.memories.setdefault(self._get_memory_key(), m)
        self.altered = True


    def edit_memory(self, user_keywords):
        m_matches = self._memory_match(user_keywords)
        m_key = self._select_memory_from_list(m_matches)
        self.memories[m_key].edit_menu()
        print('Successfully edited \'{}\''.format(self.memories[m_key].title))
        self.altered = True

    def _get_memory_key(self):
        print(self.memory_keys)
        next_key = min(self.memory_keys)
        self.memory_keys.remove(next_key)

        if len(self.memory_keys) == 0:
            self.memory_keys.add(next_key + 1)

        print(next_key, self.memory_keys)
        return next_key

    def _memory_match(self, user_keywords):
        """returns a list of (memory_key, memory_obj) tuples sorted in ascending order by relevancy to user_keywords"""
        user_keywords = set(standardize(user_keywords))

        for m in self.memories.values():
            m_keywords = m.make_set()
            m.search_score = len(user_keywords.intersection(m_keywords))

        # m_matches is a list of (m_key, m_obj) tuples sorted in ascendaing order by m_obj.search_score
        m_matches = sorted(self.memories.items(), key=lambda x: x[1])

        # reset search score for all memories so they are scored correctly next time
        for m in self.memories.values():
            m.search_score = 0

        return m_matches

    def recall_memory(self, user_keywords):
        m_matches = self._memory_match(user_keywords)
        m_key = self._select_memory_from_list(m_matches)
        print('{}\n\t{}'.format(self.memories[m_key].title, self.memories[m_key].body))

    def remove_memory(self, user_keywords):
        m_matches = self._memory_match(user_keywords)
        m_key = self._select_memory_from_list(m_matches)
        del self.memories[m_key]
        self.altered = True

    def _select_memory_from_list(self, m_matches):
        [print('{}) {}'.format(i, m.title)) for i,m in m_matches]
        print('x) Exit')
        while True:
            selection = input('> ')
            if selection == 'x':
                exit()
            elif valid_input(selection):
                selection = int(selection)
                if selection in self.memories:
                    return selection
                else:
                    print('Invalid memory selection \'{}\''.format(selection))
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
            print('1) Edit Title\n2) Edit Keywords\n3) Edit Body\n4) Done')
            selection = input('> ')

            if valid_input(selection):
                selection = int(selection)
                options = {
                    1:self.update_title,
                    2:self.update_keywords,
                    3:self.update_body,
                }

                if selection == 4:
                    if len(input('Press ENTER to Confirm')) == 0:
                        return
                else:
                    options[selection]()

    def make_set(self):
        m_data = ' '.join([self.title, self.keywords, self.body])
        return set(standardize(m_data))

def read_pkl(pkl_file):
    try:
        with open(pkl_file, 'rb') as in_stream:
            if os.path.getsize(pkl_file) > 0:
                return pickle.load(in_stream)
    except FileNotFoundError:
        print('{0} not found, creating new {0} file'.format(pkl_file))
    except Exception as e:
        print('Error occured while loading {}\n{}'.format(pkl_file, e.args))
    return None

def write_pkl(pkl_file, payload):
    try:
        with open(pkl_file, 'wb') as out_stream:
            pickle.dump(payload, out_stream, pickle.HIGHEST_PROTOCOL)
            print('Successfully saved {}'.format(pkl_file))
    except Exception as e:
        print('Error occured while saving {}\n{}'.format(pkl_file, e.args))

def main(argv):
    # print(argv)

    brain_file = 'brain.pkl'
    brain = read_pkl(brain_file)

    if not brain:
        brain = Brain()
        brain.altered = True

    # delimit words with whitespace so they can be processed at same time as stored strings
    user_keywords = ' '.join(argv['<keyword>'])

    if argv['--add']:
        # assumed that any keywords entered would be the memory title if user intent is to add a new memory
        brain.create_memory(user_keywords)
    elif argv['--remove']:
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

    if brain.altered:
        brain.altered = False
        write_pkl(brain_file, brain)

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.0.0')
    main(args)

"""
todo


"""

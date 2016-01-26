"""memfog
Usage:
  memfog.py [<keyword>...]
            [--add | --remove | --edit]
            [(<keyword>... --add | --remove | --edit)]

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
    """
    :type s: str
    :rtype: bool
    """
    return len(s) > 0 and s.isdigit() and int(s) >= 0

def default_input(prompt, prefill=''):
    """
    :type prompt: str
    :type prefill: str
    :returns: str from input prompt entry populated by default with editable text from prefill
    """
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

def strip_whitespace(s):
    """
    :type s: str
    :returns: s stripped or whitespace
    """
    return ''.join([c for c in s if c not in string.whitespace])

def strip_punctuation(s):
    """
    :type s: str
    :returns: s stripped of all punctuation no found in exclusions
    """
    exclusions = ['\'','"']
    return ''.join([c for c in s if c not in string.punctuation or c in exclusions])

def standardize(s):
    """
    :type s: str
    :returns: list of non-empty words strings from s stripped of whitespace and punctuation
    """
    stripped = strip_punctuation(s).lower()
    arr = stripped.split(' ')
    arr_no_ws = map(strip_whitespace, arr)
    return [w for w in arr_no_ws if len(w) > 0]

class Brain:
    def __init__(self):
        self.memory_keys = {1}
        self.memories = {}
        self.altered = False

    def create_memory(self, user_title=None):
        """
        :type user_title: str or None
        """
        m = Memory()

        # if user provided a title in cli args, set memory title using that entry
        if user_title:
            m.title = user_title
        # otherwise prompt them for a title entry
        else:
            m.update_title()

        m.update_keywords()
        m.update_body()

        self.memories.setdefault(self._get_memory_key(), m)
        self.altered = True

        print('Successfully added \'{}\''.format(m.title))

    def edit_memory(self, user_keywords):
        """
        :type user_keywords: str
        """
        m_matches = self._memory_match(user_keywords)
        while True:
            m_key = self._select_memory_from_list(m_matches, 'Edit')
            if m_key:
                self.memories[m_key].edit_menu()
                self.altered = True

                print('Successfully edited \'{}\''.format(self.memories[m_key].title))
            else:
                break

    def _get_memory_key(self):
        """
        :rtype: int
        :returns: smallest key from self.memory_keys
        """
        # use minimum of available memory keys so keys are consecutive
        next_key = min(self.memory_keys)
        self.memory_keys.remove(next_key)
        if len(self.memory_keys) == 0:
            self.memory_keys.add(next_key + 1)
        return next_key

    def _memory_match(self, user_keywords):
        """
        :type user_keywords: str
        :returns: self.memories dict sorted by memory_obj.search_score in ascending order
        """
        user_set = set(standardize(user_keywords))
        user_set_count = len(user_set)

        for m in self.memories.values():
            m_keywords = m.make_set()
            m_score = len(user_set.intersection(m_keywords))
            if user_set_count > 0:
                m.search_score = m_score / user_set_count * 100

        return dict(sorted(self.memories.items(), key=lambda x: x[1]))

    def display_memory(self, user_keywords):
        """
        :type user_keywords: str
        """
        m_matches = self._memory_match(user_keywords)
        while True:
            m_key = self._select_memory_from_list(m_matches, 'Display')
            if m_key:
                print('{}\n\t{}'.format(self.memories[m_key].title, self.memories[m_key].body))
            else:
                break

    def remove_memory(self, user_keywords):
        """
        :type user_keywords: str
        """
        m_matches = self._memory_match(user_keywords)
        while True:
            m_key = self._select_memory_from_list(m_matches, 'Remove')
            if m_key:
                # reclaim key of deleted memory so it can be reused
                self.memory_keys.add(m_key)

                title = self.memories.pop(m_key).title

                # remove from m_matches so deleted memory not shown in memory selection memnu
                m_matches .pop(m_key)
                self.altered = True

                print('Successfully removed \'{}\''.format(title))
            else:
                break

    def _select_memory_from_list(self, m_matches, action_description):
        """
        :type m_matches: dict
        :type action_description: str
        :returns: m_id int of selected memory or 0
        """
        if len(self.memories) > 0:
            print('{} which memory?'.format(action_description))
            [print('{}) [{}%] {}'.format(m_key, m.search_score, m.title)) for m_key,m in m_matches.items()]
            selection = input('> ')
            if valid_input(selection):
                selection = int(selection)
                if selection in self.memories:
                    return selection
                else:
                    print('Invalid memory selection \'{}\''.format(selection))
        else:
            print('No memories exist')
        return 0

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
            print('1) Edit Title\n2) Edit Keywords\n3) Edit Body')
            selection = input('> ')

            if valid_input(selection):
                selection = int(selection)
                options = {
                    1:self.update_title,
                    2:self.update_keywords,
                    3:self.update_body,
                }

                if selection not in options:
                    break
                else:
                    options[selection]()
            else:
                break

    def make_set(self):
        m_data = ' '.join([self.title, self.keywords, self.body])
        return set(standardize(m_data))

def read_pkl(pkl_file):
    """
    :type pkl_file: str
    """
    try:
        with open(pkl_file, 'rb') as in_stream:
            if os.path.getsize(pkl_file) > 0:
                return pickle.load(in_stream)
    except FileNotFoundError:
        print('{0} not found, creating new {0} file'.format(pkl_file))
    except Exception as e:
        print('Error occured while loading {}\n{}'.format(pkl_file, e.args))
    return

def write_pkl(pkl_file, payload):
    """
    :type pkl_file: str
    :type payload: Brain
    """
    try:
        with open(pkl_file, 'wb') as out_stream:
            pickle.dump(payload, out_stream, pickle.HIGHEST_PROTOCOL)
            print('Successfully saved {}'.format(pkl_file))
    except Exception as e:
        print('Error occured while saving {}\n{}'.format(pkl_file, e.args))

def main(argv):
    brain_file = 'brain.pkl'
    brain = read_pkl(brain_file)

    if not brain:
        brain = Brain()
        brain.altered = True

    # delimit words with whitespace so they can be processed at same time as memory string data
    user_keywords = ' '.join(argv['<keyword>'])

    if argv['--add']:
        # assumed that keywords entered are the memory title for the new memory being added
        brain.create_memory(user_keywords)
    elif argv['--remove']:
        brain.remove_memory(user_keywords)
    elif argv['--edit']:
        brain.edit_memory(user_keywords)
    elif len(user_keywords) > 0:
        if len(brain.memories) > 0:
            brain.display_memory(user_keywords)
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

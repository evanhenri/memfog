"""

Usage: memfog [--add|--remove|--edit] [<keyword>...] [--top <n>]
       memfog [--backup <path>]

Options:
  -h --help           Show this screen
  -v --version        Show version
  -a --add            Create new memory record
  -r --remove         List records containing keywords and remove selected
  -e --edit           List records containing keywords and edit details of selected
  -t --top <n>        Limit results to top n memories
  -b --backup <path>  Create a json backup of memory data that can be imported

"""
from docopt import docopt
from fuzzywuzzy import fuzz
import datetime
import readline
import pickle
import jsonpickle
import string
import shlex
import json
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
    arr = shlex.split(stripped)
    arr_no_ws = map(strip_whitespace, arr)
    return [w for w in arr_no_ws if len(w) > 0]

def user_cofirm(msg=''):
    """
    :rtype: bool
    """
    return input('Confirm {} - y/n?\n> '.format(msg)).lower() == 'y'

class Brain:
    def __init__(self):
        self.memory_keys = {1}
        self.memories = {}
        self.altered = False
        self.top_n = 0

    def backup(self, backup_path):
        if not os.path.exists(backup_path):
            print('{} does not exist, saving backup to {}'.format(backup_path, os.getcwd()))
            backup_path = os.getcwd()

        elif backup_path[-1] != '/':
            backup_path += '/'

        date = datetime.datetime.now()
        backup_path += 'memfog_{}-{}-{}.json'.format(date.month, date.day, date.year)

        if os.path.isfile(backup_path):
            if not user_cofirm('overwrite of existing file {}'.format(backup_path)):
                return

        mems = ''.join(map(jsonpickle.encode, self.memories.values()))
        str_to_file(backup_path, mems)

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
        user_set = ''.join(set(standardize(user_keywords)))

        for m in self.memories.values():
            m_keywords = ' '.join(m.make_set())
            m.search_score = fuzz.token_sort_ratio(m_keywords, user_set)

        return [*sorted(self.memories.items(), key=lambda x: x[1])]

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

                m = self.memories.pop(m_key)

                # remove from m_matches so deleted memory not shown in memory selection memnu
                m_matches.remove((m_key, m))
                self.altered = True

                print('Successfully removed \'{}\''.format(m.title))
            else:
                break

    def _select_memory_from_list(self, m_matches, action_description):
        """
        :type m_matches: list
        :type action_description: str
        :returns: m_id int of selected memory or 0
        """
        if len(self.memories) > 0:
            print('{} which memory?'.format(action_description))

            for m_key,m in m_matches[-self.top_n::]:
                print('{}) [{}%] {}'.format(m_key, m.search_score, m.title))

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

def pkl_from_file(file_path):
    """
    :type file_path: str
    """
    try:
        with open(file_path, 'rb') as in_stream:
            if os.path.getsize(file_path) > 0:
                return pickle.load(in_stream)
    except FileNotFoundError:
        print('{0} not found, creating new {0} file'.format(file_path))
    except Exception as e:
        print('Error occured while loading {}\n{}'.format(file_path, e.args))
    return

def pkl_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: Brain
    """
    try:
        with open(file_path, 'wb') as out_stream:
            pickle.dump(payload, out_stream, pickle.HIGHEST_PROTOCOL)
            print('Successfully saved {}'.format(file_path))
    except Exception as e:
        print('Error occured while exporting to {}\n{}'.format(file_path, e.args))

def str_from_file(file_path):
    """
    :type file_path: str
    :retuers: contents of file at file_path as str
    """
    with open(file_path, 'r') as f:
        return f.read()

def str_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: str
    """
    try:
        with open(file_path, 'w') as f:
            f.write(payload)
        print('Export to {} successfull'.format(file_path))
    except Exception as e:
        print('Error occured while exporting to {}\n{}'.format(file_path, e.args))

def main(argv):
    brain_file = 'brain.pkl'
    brain = pkl_from_file(brain_file)
    print(argv)

    if not brain:
        brain = Brain()
        brain.altered = True

    top_n = argv['--top']
    if top_n:
        top_n = top_n[0]
        if valid_input(top_n):
            brain.top_n = int(top_n)
        else:
            print('Invalid threshold value \'{}\''.format(top_n))

    # delimit words with whitespace so they can be processed at same time as memory string data
    user_keywords = ' '.join(argv['<keyword>'])

    if argv['--add']:
        # assumed that keywords entered are the memory title for the new memory being added
        brain.create_memory(user_keywords)
    elif argv['--remove']:
        brain.remove_memory(user_keywords)
    elif argv['--edit']:
        brain.edit_memory(user_keywords)
    elif argv['--backup']:
        brain.backup(argv['--backup'])
    elif len(brain.memories) > 0:
        brain.display_memory(user_keywords)
    else:
        print('No memories exist')

    if brain.altered:
        brain.altered = False
        pkl_to_file(brain_file, brain)

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.0.0')
    main(args)

"""
todo


"""

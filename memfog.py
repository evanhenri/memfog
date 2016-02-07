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
import datetime
import os
import shlex
import string
from docopt import docopt
from fuzzywuzzy import fuzz

from src import io, user

def is_valid_input(s):
    """
    :type s: str
    :rtype: bool
    """
    return len(s) > 0 and s.isdigit() and int(s) >= 0

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
    return shlex.shlex(stripped)

class Brain:
    def __init__(self):
        self.memory_keys = {1}
        self.memories = {}

        # flag used to determine if brain.pkl must be re-written
        self.altered = False
        self.top_n = 10

    def backup_memories(self, dir_path):
        if not dir_path:
            dir_path = os.getcwd()
        elif not os.path.exists(dir_path):
            print('{} does not exist'.format(dir_path))
            dir_path = os.getcwd()

        if dir_path[-1] != '/':
            dir_path += '/'

        date = datetime.datetime.now()
        dir_path += 'memfog_{}-{}-{}.json'.format(date.month, date.day, date.year)

        if os.path.isfile(dir_path):
            if not user.confirm('overwrite of existing file {}'.format(dir_path)):
                return

        m_json = [m.get_backup() for m in self.memories.values()]
        io.json_to_file(dir_path, m_json)

    def create_memory(self, user_title=None):
        """
        :type user_title: str or None
        """
        m = Memory()

        # prevent spewing of exception if ^c used to cancel adding a memory
        try:
            # if user provided a title in cli args, set memory title using that entry
            if user_title:
                m.title = user_title
            # otherwise prompt them for a title entry
            else:
                m.update_title()

            m.update_keywords()
            m.update_body()
        except KeyboardInterrupt:
            print('\nDiscarded new memory data')
            return

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
                input('...')
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

    def import_memories(self, file_path):
        """
        :type file_path: str
        """
        json_memories = io.json_from_file(file_path)

        for json_m in json_memories:
            m = Memory()
            m.title = json_m['title']
            m.keywords = json_m['keywords']
            m.body = json_m['body']
            self.memories.setdefault(self._get_memory_key(), m)
        self.altered = True

        print('Successfully imported {} memories'.format(len(json_memories)))

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

            if is_valid_input(selection):
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

    def get_backup(self):
        return {k:v for k,v in self.__dict__.items() if k != 'search_score'}

    def edit_menu(self):
        while True:
            print('1) Edit Title\n2) Edit Keywords\n3) Edit Body')
            selection = input('> ')

            if is_valid_input(selection):
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
        m_data = ' '.join([self.title, self.keywords])
        return set(standardize(m_data))

    def update_title(self):
        self.title = user.prefilled_input('Title: ', self.title)

    def update_keywords(self):
        self.keywords = user.prefilled_input('Keywords: ', self.keywords)

    def update_body(self):
        self.body = user.prefilled_input('Body: ', self.body)

def main(argv):
    brain_file = '{}/brain.pkl'.format(os.path.dirname(os.path.realpath(__file__)))
    brain = io.pkl_from_file(brain_file)

    if not brain:
        brain = Brain()
        brain.altered = True

    top_n = argv['--top']
    if top_n:
        if is_valid_input(top_n):
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
        brain.backup_memories(argv['<path>'])
    elif argv['--import']:
        brain.import_memories(argv['<path>'])
    elif len(brain.memories) > 0:
        brain.display_memory(user_keywords)
    else:
        print('No memories exist')

    if brain.altered:
        brain.altered = False
        io.pkl_to_file(brain_file, brain)

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.0.1')
    main(args)

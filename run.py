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
import os

def default_input(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)
   finally:
      readline.set_startup_hook()

def non_empty_str(s):
    return len(s) > 0

class Node:
    def __init__(self, title, phrases, keywords, body):
        self.title = title
        self.phrases = list(phrases)
        self.keywords = list(keywords)
        self.body = body

class Memory:
    def __init__(self):
        self.title = ''
        self.phrases = ''
        self.keywords = ''
        self.body = ''
        self.memory_file = 'memories.pkl'

    def _construct_memory(self):
        self.phrases = self.phrases.split(',')
        self.phrases = [p.lstrip().rstrip() for p in self.phrases]
        self.phrases = filter(non_empty_str, self.phrases)

        self.keywords = self.keywords.split(',')
        self.keywords = [k.lstrip().rstrip() for k in self.keywords]
        self.keywords = filter(non_empty_str, self.keywords)

        return Node(self.title, self.phrases, self.keywords, self.body)

    def _update_memory(self):
        self.phrases = [p.lstrip().rstrip() for p in self.phrases]
        self.phrases = filter(non_empty_str, self.phrases)

        self.keywords = [k.lstrip().rstrip() for k in self.keywords]
        self.keywords = filter(non_empty_str, self.keywords)

        return Node(self.title, self.phrases, self.keywords, self.body)

    def _edit_menu(self, update_mode=False):
        print('0) Edit Title\n1) Edit Phrases\n2) Edit Keywords\n'
              '3) Edit Body\n4) Save\n5) Cancel')

        opts = {0:self.update_title, 1:self.update_phrases,
                2:self.update_keywords, 3:self.update_body}

        selection = input('> ')

        while True:
            if len(selection) > 0 and selection.isdigit():
                selection = int(selection)
                if 0 <= selection < len(opts):
                    opts[selection]()
                elif selection == 4:
                    if update_mode: self._update_memory()
                    else: self._construct_memory()
                    break
                elif input('Confirm cancel y/n: ') == 'y':
                    break
            else:
                print('Invalid entry')

    def create(self):
        self.update_title()
        self.update_phrases()
        self.update_keywords()
        self.update_body()
        self._edit_menu()

    def edit(self, *args):
        memories = self._sort_by_matches(*args)
        if not memories:
            print('No memories exist')
            return

        for i,item in enumerate(memories):
            print('{}) {}'.format(i, item.title))

        selection = input('> ')

        if len(selection) > 0 and selection.isdigit():
            selection = int(selection)
            self.title = memories[selection].title
            self.phrases = memories[selection].phrases
            self.keywords = memories[selection].keywords
            self.body = memories[selection].body

            print(self.title, self.phrases, self.keywords, self.body)

            self._edit_menu(update_mode=True)

    def _load(self):
        try:
            with open(self.memory_file, 'rb') as in_stream:
                if os.path.getsize(self.memory_file) > 0:
                    return pickle.load(in_stream)
                return
        except FileNotFoundError:
            return

    def recall(self, *args):
        memories = self._sort_by_matches(*args)
        if not memories:
            print('No memories exist')
            return

        for i,item in enumerate(memories):
            print('{}) {}'.format(i, item.title))

        selection = input('> ')
        if len(selection) > 0 and selection.isdigit():
            selection = int(selection)
            memory = memories[selection]
            print('{}\n\n{}'.format(memory.title, memory.body))
        else:
            print('Invalid entry')

    def remove(self, *args):
        memories = self._sort_by_matches(*args)
        if not memories:
            print('No memories exist')
            return

        for i,item in enumerate(memories):
            print('{}) {}'.format(i, item.title))

        selection = input('> ')

        if len(selection) > 0 and selection.isdigit():
            selection = int(selection)
            print('Removed \'{}\''.format(memories[selection].title))
            if 0 < selection < len(memories):
                memories.pop(selection)

        self.save_updated_memories(memories)

    def _sort_by_matches(self, *args):
        memories = self._load()
        if not memories:
            return

        matches = []
        for memory in memories:
            score = 0
            for item in args:
                if any([item in memory.title, item in memory.phrases, item in memory.keywords, item in memory.body]):
                    score += 1
            matches.append(score)

        # zip object with their respective count of matching words
        lst_tuples = zip(matches, memories)

        # sort the tuples by memories with most matching words
        sorted_tuple = sorted(lst_tuples, key=lambda x: x[0], reverse=True)

        # unzip the tuple and only return the now sorted list of memories
        return list(list(zip(*sorted_tuple))[1])

    def save_new_memory(self, new_memory):
        memories = self._load()
        if memories: memories.append(new_memory)
        else: memories = [new_memory]
        self.save_updated_memories(memories)

    def save_updated_memories(self, memories):
        with open(self.memory_file, 'wb') as out_stream:
            pickle.dump(memories, out_stream, pickle.HIGHEST_PROTOCOL)

    def update_body(self):
        self.body = default_input('Body: ', self.body)
    def update_keywords(self):
        self.keywords = default_input('Keywords: ', self.keywords)
    def update_phrases(self):
        self.phrases = default_input('Phrases: ', self.phrases)
    def update_title(self):
        self.title = default_input('Title: ', self.title)

def main(argv):
    print(argv)

    memory = Memory()

    if argv['--add']:
        memory.create()
    elif argv['--rm']:
        memory.remove(*argv['<keyword>'])
    elif argv['--edit']:
        memory.edit(*argv['<keyword>'])
    else:
        memory.recall(*argv['<keyword>'])

if __name__ == '__main__':
    args = docopt(__doc__, version='memfog v1.0.0')
    main(args)

"""
todo

if try to edit, old values do not appear for some sections like phrases and keywords, issue with lists?

error occurs for line 72, TypeError: object of type 'int' has no len() - not sure why

"""

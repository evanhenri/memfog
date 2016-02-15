from fuzzywuzzy import fuzz
import datetime
import os

from . import io, user, data
from . import memory

class Brain:
    def __init__(self, mem_db_path):
        self.mem_db = io.DB(mem_db_path)
        self.memories = [memory.Memory(key,t,k,b) for key,t,k,b in self.mem_db.dump()]
        self.top_n = 10

        # words to omit from fuzzy string search, e.g. and the is are etc.
        self.excluded_words = set()

    def backup_memories(self, dir_path):
        """
        :type dir_path: str
        """
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

        m_json = [Mem.get_backup() for Mem in self.memories]
        io.json_to_file(dir_path, m_json)

    def create_memory(self, user_title=None):
        """
        :type user_title: str or None
        """
        Mem = memory.Memory()
        try:
            # if user provided a title in cli args, set memory title using that entry
            if user_title: Mem.title = user_title
            else: Mem.update_title()
            Mem.update_keywords()
            Mem.update_body()

        except KeyboardInterrupt:
            print('\nDiscarded new memory data')
            return
        self.mem_db.insert(Mem.title, Mem.keywords, Mem.body)

    def display_memory(self, user_keywords):
        """
        :type user_keywords: str
        """
        m_matches = self._memory_match(user_keywords)
        while True:
            Mem = self._select_memory_from_list(m_matches, 'Display')
            if Mem:
                mem_ui = memory.UI(Mem.title, Mem.keywords, Mem.body)
            else:
                break

    def edit_memory(self, user_keywords):
        """
        :type user_keywords: str
        """
        m_matches = self._memory_match(user_keywords)
        while True:
            Mem = self._select_memory_from_list(m_matches, 'Edit')
            if Mem:
                print('1) Edit Title\n2) Edit Keywords\n3) Edit Body')
                selection = user.get_input()

                if selection:
                    options = { 1:Mem.update_title, 2:Mem.update_keywords, 3:Mem.update_body }
                    attr = { 1:'title', 2:'keywords', 3:'body' }

                    if selection not in options:
                        break
                    else:
                        # call memory method to change its value
                        options[selection]()

                        # update changed attribute of Mem in db
                        self.mem_db.update(Mem.db_key, attr[selection], eval('Mem.{}'.format(attr[selection])))
            else:
                break

    def import_memories(self, file_path):
        """
        :type file_path: str
        """
        json_memories = io.json_from_file(file_path)
        [self.mem_db.insert(mem['title'], mem['keywords'], mem['body']) for mem in json_memories]
        print('Imported {} memories'.format(len(json_memories)))

    def _memory_match(self, user_keywords):
        """
        :type user_keywords: str
        :returns: top_n Memories in self.memories list sorted by Memory.search_score in ascending order
        """
        user_set = ''.join(set(data.standardize(user_keywords)))

        for Mem in self.memories:
            m_words = Mem.make_set()

            # remove exluded words from being considered in memory matching
            m_words.difference_update(self.excluded_words)

            m_keywords = ' '.join(m_words)
            Mem.search_score = fuzz.token_sort_ratio(m_keywords, user_set)
        return [*sorted(self.memories)][-self.top_n::]

    def remove_memory(self, user_keywords):
        """
        :type user_keywords: str
        """
        m_matches = self._memory_match(user_keywords)
        while True:
            Mem = self._select_memory_from_list(m_matches, 'Remove')
            if Mem:
                self.mem_db.remove(Mem.db_key)
                self.memories.remove(Mem)
                m_matches.remove(Mem)
            else:
                break

    def _select_memory_from_list(self, m_matches, action_description):
        """
        :type m_matches: list
        :type action_description: str
        :returns: Memory object or None
        """
        if len(self.memories) > 0:
            print('{} which memory?'.format(action_description))

            for i,Mem in enumerate(m_matches):
                print('{}) [{}%] {}'.format(i, Mem.search_score, Mem.title))

            selection = user.get_input()

            if selection is not None:
                if selection < len(self.memories):
                    return m_matches[selection]
                else:
                    print('Invalid memory selection \'{}\''.format(selection))
        else:
            print('No memories exist')
        return None
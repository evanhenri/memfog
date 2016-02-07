from fuzzywuzzy import fuzz
import datetime
import os

from . import io, user, data, memory

class Brain:
    def __init__(self):
        self.memory_keys = {1}
        self.memories = {}

        # flag used to determine if brain.pkl must be re-written
        self.altered = False
        self.top_n = 10

        # words to omit from fuzzy string search, e.g. and the is are etc.
        self.excluded_words = set()

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
        m = memory.Memory()

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
            m = memory.Memory()
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
        user_set = ''.join(set(data.standardize(user_keywords)))

        for m in self.memories.values():
            m_words = m.make_set()

            # remove exluded words from being considered in memory matching
            m_words.difference_update(self.excluded_words)

            m_keywords = ' '.join(m_words)
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

            if data.is_valid_input(selection):
                selection = int(selection)
                if selection in self.memories:
                    return selection
                else:
                    print('Invalid memory selection \'{}\''.format(selection))
        else:
            print('No memories exist')
        return 0
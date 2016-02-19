from fuzzywuzzy import fuzz
import datetime
import os

from . import io, user, data, memory

class Brain:
    def __init__(self):
        self.data_dir = 'datadir/'
        self.body_dir = self.data_dir + 'body/'

        io.init_dir(self.data_dir)
        io.init_dir(self.body_dir)
        io.init_file(self.data_dir + 'exclusions.txt')

        self.excluded_words = io.set_from_file(self.data_dir + 'exclusions.txt')
        self.mem_db = io.DB(self.data_dir + 'memories.db')
        self.memories = [memory.Memory(*record) for record in self.mem_db.dump()]
        self.top_n = 10

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

    def create_memory(self):
        try:
            # display UI so user can fill in memory data
            Mem = memory.Memory()
            Mem_UI = memory.UI(Mem)
            Mem.__dict__.update(Mem_UI.__dict__)

            db_key = self.mem_db.insert(Mem)
            io.str_to_file(self.body_dir + str(db_key), Mem.body)

        except KeyboardInterrupt:
            print('Discarded new memory data')
            return

    def display_memory(self, user_keywords):
        """
        :type user_keywords: str
        """
        m_matches = self._memory_match(user_keywords)
        while True:
            Mem = self._select_memory_from_list(m_matches, 'Display')
            if Mem:
                try:
                    Mem.body = io.str_from_file(self.body_dir + str(Mem.db_key))

                    Mem_UI = memory.UI(Mem)
                    changed_values = Mem.diff(Mem_UI)

                    if 'body' in changed_values:
                        io.str_to_file(self.body_dir + str(Mem.db_key), Mem_UI.body)

                        # remove body so it is not present when dict is passed to mem_db.update_many
                        changed_values.pop('body')

                    if len(changed_values) > 0:
                        self.mem_db.update_many(Mem.db_key, changed_values)

                except KeyboardInterrupt:
                    pass
            else:
                break

    def import_memories(self, file_path):
        """
        :type file_path: str
        """
        json_memories = io.json_from_file(file_path)

        for record in json_memories:
            Mem = memory.Memory()
            Mem.__dict__.update(record)
            db_key = self.mem_db.insert(Mem)
            io.str_to_file(self.body_dir + str(db_key), Mem.body)

        print('Imported {} memories'.format(len(json_memories)))

    def _memory_match(self, user_keywords):
        """
        :type user_keywords: str
        :returns: top_n Memories in self.memories list sorted by Memory.search_score in ascending order
        """
        user_set = ''.join(set(data.standardize(user_keywords)))

        for Mem in self.memories:
            m_words = Mem.make_set()

            # exluded words are not considered in memory matching
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
            if Mem and user.confirm('delete'):
                # delete memory record in db
                self.mem_db.remove(Mem.db_key)

                # delete body file in datadir
                io.delete_file(self.body_dir + str(Mem.db_key))

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
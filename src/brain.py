from fuzzywuzzy import fuzz
import datetime
import os

from . import io, fs, user, util
from .memory import Memory, UI

class Brain:
    def __init__(self, config):
        self.config = config
        self.excluded_words = io.set_from_file(self.config.exclusions_file_path)
        self.mem_db = io.DB(self.config.mem_db_path)
        self.memories = dict()

        for record in self.mem_db.dump():
            Mem = Memory(*record)
            self.memories[Mem.title] = Mem

    def export_mem(self, export_path):
        """
        :type export_path: str
        """
        if export_path is None or not os.path.exists(export_path):
            export_path = os.getcwd()

        date = datetime.datetime.now()
        export_file = 'memfog_{}-{}-{}.json'.format(date.month, date.day, date.year)
        export_dir = fs.validate_dir_path(export_path, os.getcwd())
        export_path = export_dir + export_file

        if os.path.isfile(export_path):
            if not user.prompt_yn('Overwrite existing file {}'.format(export_path)):
                return

        mem_data = [Mem.get_backup() for Mem in self.memories.values()]
        io.json_to_file(export_path, mem_data)

    def create_mem(self):
        Mem = Memory()

        # display UI so user can fill in memory data
        Mem_UI = UI(Mem)

        if Mem_UI.altered:
            Mem.__dict__.update(Mem_UI.__dict__)
            db_key = self.mem_db.insert(Mem)
            io.str_to_file(self.config.body_dir_path + str(db_key), Mem.body)

    def display_mem(self, user_keywords):
        """
        :type user_keywords: str
        """
        mem_fuzz_matches = self._fuzzy_match(user_keywords)
        while True:
            Mem = self.select_mem(mem_fuzz_matches, 'Display')

            # Mem is None when user enters an invalid memory selection or hits ENTER with no selection
            if Mem is not None:
                Mem.body = io.str_from_file(self.config.body_dir_path + str(Mem.db_key))
                Mem_UI = UI(Mem)

                # get memory attributes that have changed that require saving
                changed_values = Mem.diff(Mem_UI)

                if 'body' in changed_values:
                    io.str_to_file(self.config.body_dir_path + str(Mem.db_key), Mem_UI.body)

                    # remove body because if other attributes have changed, changed_values
                    #   gets passed to mem_db.update_many to write the passed in dict to the db
                    changed_values.pop('body')

                if len(changed_values) > 0:
                    self.mem_db.update(Mem.db_key, changed_values)
            else:
                break

    def import_mem(self, file_path):
        """
        :type file_path: str
        """
        json_memories = io.json_from_file(file_path)
        skipped_memories = 0

        for record in json_memories:
            Mem = Memory()
            Mem.__dict__.update(record)

            if Mem.title in self.memories:
                if self.config.force_import:
                    body_path = self.config.body_dir_path + str(self.memories[Mem.title].db_key)
                    io.str_to_file(body_path, Mem.body)
                else:
                    skipped_memories += 1
                    print('Skipping duplicate - {}'.format(Mem.title))
            else:
                db_key = self.mem_db.insert(Mem)
                io.str_to_file(self.config.body_dir_path + str(db_key), Mem.body)

        if skipped_memories > 0:
            print('Imported {}, Skipped {}'.format(len(json_memories) - skipped_memories, skipped_memories))
        else:
            print('Imported {}'.format(len(json_memories) - skipped_memories))

    def _fuzzy_match(self, user_input):
        """
        :type user_input: str
        :returns: top_n Memories in self.memories list sorted by Memory.search_score in ascending order
        """
        user_search_str = ''.join(set(util.standardize(user_input)))

        for Mem in self.memories.values():
            mem_search_set = Mem.make_set()
            mem_search_set.difference_update(self.excluded_words)
            mem_search_str = ' '.join(mem_search_set)
            Mem.search_score = fuzz.token_set_ratio(mem_search_str, user_search_str)

        return [*sorted(self.memories.values())][-self.config.top_n::]

    def remove_mem(self, user_input):
        """
        :type user_input: str
        """
        while True:
            mem_fuzz_matches = self._fuzzy_match(user_input)
            Mem = self.select_mem(mem_fuzz_matches, 'Remove')

            if Mem and user.prompt_yn('Delete {}'.format(Mem.title)):
                # delete memory record in db
                self.mem_db.remove(Mem.db_key)

                # delete body file in datadir
                io.delete_file(self.config.body_dir_path + str(Mem.db_key))

                del self.memories[Mem.title]
                mem_fuzz_matches.remove(Mem)
            else:
                break

    def select_mem(self, mem_fuzz_matches, action_description):
        """
        :type mem_fuzz_matches: list
        :type action_description: str
        :returns: Memory object or None
        """
        if len(self.memories) > 0:
            print('{} which memory?'.format(action_description))

            for i,Mem in enumerate(mem_fuzz_matches):
                print('{}) [{}%] {}'.format(i, Mem.search_score, Mem.title))

            selection = user.get_input()

            if selection is not None:
                if selection < len(self.memories):
                    return mem_fuzz_matches[selection]
                else:
                    print('Invalid memory selection \'{}\''.format(selection))
        else:
            print('No memories exist')
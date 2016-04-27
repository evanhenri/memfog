import re
import os
import subprocess

from . import file_io


class DataItem:
    def __init__(self, text):
        self.text = text
        self.instructions = []
        self.starting_state = hash(self.text)

    def is_altered(self):
        return self.starting_state != hash(self.text)


class Title(DataItem):
    def __init__(self, text):
        super(Title, self).__init__(text)

class Keywords(DataItem):
    def __init__(self, text):
        super(Keywords, self).__init__(text)

class Body(DataItem):
    def __init__(self, text):
        super(Body, self).__init__(text)


class Raw:
    def __init__(self, record):
        self.title = Title(record.title)
        self.keywords = Keywords(record.keywords)
        self.body = Body(record.body)

    def dump(self):
        return { 'title':self.title.text, 'keywords':self.keywords.text, 'body':self.body.text }

    def get_altered_attr(self):
        altered_attributes = set()
        for attr_id in ['title', 'keywords', 'body']:
            attr = getattr(self, attr_id)
            if hash(attr.text) != attr.starting_hash:
                altered_attributes.add(attr_id)
        return altered_attributes

    def update(self, args):
        for attr_id, attr_val in args.items():
            self.__dict__[attr_id].text = attr_val


class Interpreted(Raw):
    def __init__(self, record):
        super(Interpreted, self).__init__(record)
        self._pattern = re.compile(
            """                 # ?: denotes non-capture group - group that must be matched but excluded from the result
                (?:\[)          # Match \[
                (PATH|EXEC)     # Text between braces can be either PATH or EXEC
                (?:\]\()        # Match \]\(
                (.*?)           # >= 0 characters between parenthesis
                (?:\))          # Macth \)
            """, re.VERBOSE)

        self.title = self._interpret(self.title)
        self.keywords = self._interpret(self.keywords)
        self.body = self._interpret(self.body)

    def _interpret(self, data_item):
        for match in self._pattern.finditer(data_item.text):
            key, val = match.groups()
            val = ' '.join(map(os.path.expanduser, val.split()))
            data_item.instructions.append(tuple([key, val]))

            if key == 'PATH':
                file_content = file_io.str_from_file(val)
                data_item.text = data_item.text.replace(match.group(0), file_content)

            elif key == 'EXEC':
                proc = subprocess.Popen(val, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                std_out, std_err = proc.communicate(timeout=5)
                proc.wait(timeout=5)
                proc_result = std_out.decode() + std_err.decode()
                data_item.text = data_item.text.replace(match.group(0), proc_result)

        # even though instruction is interpretted properly, some instructions still exist in output in addition
        # to their interpretted text. Substitute with empty string temporarily so they don't appear in UI
        data_item.text = re.sub(self._pattern, '', data_item.text)
        return data_item

    def update_sources(self):
        if self.title.is_altered():
            for key,val in self.title.instructions:
                if key == 'PATH':
                    file_io.str_to_file(val, self.title.text)
        if self.keywords.is_altered():
            for key,val in self.keywords.instructions:
                if key == 'PATH':
                    file_io.str_to_file(val, self.keywords.text)
        if self.body.is_altered():
            for key,val in self.body.instructions:
                if key == 'PATH':
                    file_io.str_to_file(val, self.body.text)

class Data:
    def __init__(self, record):
        self.rec_id = record.row_id

        self.raw = Raw(record)
        self.interpreted = Interpreted(record)
        self.is_interpreted = self.raw.dump() != self.interpreted.dump()

    def get_altered_fields(self):
        rec = {}
        if self.is_interpreted:
            if self.interpreted.title.is_altered():
                rec['title'] = self.interpreted.title.text
            if self.interpreted.keywords.is_altered():
                rec['keywords'] = self.interpreted.keywords.text
            if self.interpreted.body.is_altered():
                rec['body'] = self.interpreted.body.text
        else:
            if self.raw.title.is_altered():
                rec['title'] = self.raw.title.text
            if self.raw.keywords.is_altered():
                rec['keywords'] = self.raw.keywords.text
            if self.raw.body.is_altered():
                rec['body'] = self.raw.body.text
        return rec









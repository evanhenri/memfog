import re
import os
import subprocess

from . import file_io


class Title:
    def __init__(self, text):
        self.text = text
        self.starting_hash = hash(self.text)

class Keywords:
    def __init__(self, text):
        self.text = text
        self.starting_hash = hash(self.text)

class Body:
    def __init__(self, text):
        self.text = text
        self.starting_hash = hash(self.text)

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

        self.title.text = self._process(self.title.text)
        self.keywords.text = self._process(self.keywords.text)
        self.body.text = self._process(self.body.text)

    def _process(self, s):
        for match in self._pattern.finditer(s):
            key, val = match.groups()
            val = ' '.join(map(os.path.expanduser, val.split()))

            if key == 'PATH':
                file_content = file_io.str_from_file(val)
                s = s.replace(match.group(0), file_content)

            elif key == 'EXEC':
                proc = subprocess.Popen(val, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                std_out, std_err = proc.communicate(timeout=5)
                proc.wait(timeout=5)
                proc_result = std_out.decode() + std_err.decode()
                s = s.replace(match.group(0), proc_result)

        # even though instruction is interpretted properly, some instructions still exist in output in addition
        # to their interpretted text. Substitute with empty string temporarily so they don't appear in UI
        s = re.sub(self._pattern, '', s)
        return s

class Data:
    def __init__(self, record):
        self.raw = Raw(record)
        self.interpreted = Interpreted(record)
        self.is_interpreted = self.raw.dump() != self.interpreted.dump()




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
        self.__dict__.update(args)

class Interpreted(Raw):
    def __init__(self, record):
        super(Interpreted, self).__init__(record)
        self._pattern = re.compile('(?:\[)(PATH|EXEC)(?:\]\()(.*?)(?:\))')

        [self._process(attr) for attr in ['title','keywords','body']]


    def _process(self, attr_id):
        attr = getattr(self, attr_id)
        text = getattr(attr, 'text')

        for match in self._pattern.finditer(text):
            key, val = match.groups()
            val = ' '.join(map(os.path.expanduser, val.split()))

            if key == 'PATH':
                text = text.replace(match.group(0), file_io.str_from_file(val))

            elif key == 'EXEC':
                print('!!!')
                proc = subprocess.Popen(val, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                std_out, std_err = proc.communicate(timeout=5)
                text = text.replace(match.group(0), std_out.decode() + std_err.decode())
                print(text)

            self.__dict__[attr_id].text = text
            #FIXME PATH and EXEC output are being interpretted successfully, but embedded instruction still appears in text
            # in addition to interpretted content


class Data:
    def __init__(self, record):
        self.raw = Raw(record)
        self.interpreted = Interpreted(record)
        self.is_interpreted = self.raw.dump() != self.interpreted.dump()




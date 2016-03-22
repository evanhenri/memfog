import re

from . import file_io

class Link:
    def __init__(self):
        keys = '|'.join(['PATH'])
        # capture key and value when found in [key](value) format and key is in keys
        self._pattern = re.compile('(?:\[)('+keys+')(?:\]\()(.*?)(?:\))')

    def expand(self, s):
        for match in self._pattern.finditer(s):
            key, value = match.groups()

            if key == 'PATH':
                # replace [PATH](fp) in Record.body with the contents of the file at fp
                s = s.replace(match.group(0), file_io.str_from_file(value))

        return s

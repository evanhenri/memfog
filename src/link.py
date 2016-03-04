import re
import github3

from . import file_io

class Link:
    def __init__(self):
        keys = '|'.join(['GIST','PATH'])
        # capture key and value when found in [key](value) format and key is in keys
        self.prog = re.compile('(?:\[)('+keys+')(?:\]\()(.*?)(?:\))')

    def expand(self, s):
        for match in self.prog.finditer(s):
            key, value = match.groups()

            if key == 'PATH':
                # replace [PATH](fp) in Record.body with the contents of the file at fp
                s = s.replace(match.group(0), file_io.str_from_file(value))

            elif key == 'GIST':
                gist = github3.gist(value)
                g = ''.join([str(f.content()) for f in gist.files()])
                s = s.replace(match.group(0), g)

        return s







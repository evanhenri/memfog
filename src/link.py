import re
import os
import subprocess

from . import file_io

class Link:
    def __init__(self):
        keys = '|'.join(['PATH', 'EXEC'])
        # capture key and value when found in [key](value) format and key is in keys
        self._pattern = re.compile('(?:\[)('+keys+')(?:\]\()(.*?)(?:\))')

    def expand(self, s):
        for match in self._pattern.finditer(s):
            key, value = match.groups()
            value = os.path.expanduser(value)

            if key == 'PATH':
                # replace [PATH](fp) in Record.body with the contents of the file at fp
                s = s.replace(match.group(0), file_io.str_from_file(value))
            elif key == 'EXEC':
                args = [os.path.expanduser(v) for v in value.split()]
                proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                s, errs = map(lambda x: x.decode("utf-8"), proc.communicate(timeout=5))
                if len(errs) > 0:
                    s += '\n\n' + errs.decode("utf-8")
        return s

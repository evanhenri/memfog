import re
import os
import subprocess

from . import file_io

keys = '|'.join(['PATH', 'EXEC'])
# capture key and value when found in [key](value) format and key is in keys
_pattern = re.compile('(?:\[)(' + keys + ')(?:\]\()(.*?)(?:\))')


def expand(s):
    for match in _pattern.finditer(s):
        key, value = match.groups()
        value = os.path.expanduser(value)

        if key == 'PATH':
            # replace [PATH](fp) in Record.body with the contents of the file at fp
            s = s.replace(match.group(0), file_io.str_from_file(value))
        elif key == 'EXEC':
            proc = subprocess.Popen(value, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            s, errors = proc.communicate(timeout=5)
            s += errors
    return s

def extract(s):
    for match in _pattern.finditer(s):
        return match.groups()



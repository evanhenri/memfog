import json

from . import memfog
from . import file_sys


def json_from_file(fp):
    """
    :type fp: pathlib.Path or str
    """
    fp = file_sys.Path(fp)

    if len(fp.parts) == 1:
        fp = memfog.config.project_dp + fp
    try:
        if fp.exists():
            with open(str(fp), 'r') as f:
                return json.load(f)
        return dict()
    except Exception as e:
        return 'Error occured while reading {} as json\n{}'.format(str(fp), e.args)

def json_to_file(fp, content):
    """
    :type fp: pathlib.Path or str
    :type content: json encodable object
    """
    fp = file_sys.Path(fp)

    if len(fp.parts) == 1:
        fp = memfog.config.project_dp + fp
    try:
        with open(str(fp), 'w') as f:
            json.dump(content, f, indent=4)
        return 'Successfully wrote to {}'.format(str(fp))
    except Exception as e:
        return 'Unable to write json to {}\n{}'.format(str(fp), e.args)

def str_from_file(fp):
    """
    :type fp: pathlib.Path or str
    :returns: contents of file at file_path as string
    """
    fp = file_sys.Path(fp)

    if len(fp.parts) == 1:
        fp = memfog.config.project_dp / fp
    try:
        if fp.exists():
            with open(str(fp), 'r') as f:
                return f.read()
        return str()
    except Exception as e:
        return 'Error occured while reading {} as string\n{}'.format(str(fp), e.args)

def str_to_file(fp, content):
    """
    :type fp: pathlib.Path or str
    :type content: str
    """
    fp = file_sys.Path(fp)

    if len(fp.parts) == 1:
        fp = memfog.config.project_dp + fp
    try:
        with open(str(fp), 'w') as f:
            f.write(content)
    except Exception as e:
        return 'Error occured while reading {} as set\n{}'.format(str(fp), e.args)
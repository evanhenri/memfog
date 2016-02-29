import os
import json

from . import file_sys

def delete_file(fp):
    """
    :type fp: str
    """
    try:
        if file_sys.file_exists(fp):
            os.remove(fp)
    except Exception as e:
        print('Error occured while deleting {}\n{}'.format(fp, e.args))

def json_from_file(fp):
    """
    :type fp: str
    """
    try:
        if file_sys.file_exists(fp):
            with open(fp, 'r') as f:
                return json.load(f)
        return dict()
    except Exception as e:
        print('Error occured while reading {} as json\n{}'.format(fp, e.args))

def json_to_file(fp, content):
    """
    :type fp: str
    :type content: json encodable obj
    """
    try:
        with open(fp, 'w') as f:
            json.dump(content, f, indent=4)
        print('Saved {}'.format(fp))
    except Exception as e:
        print('Error occured while writing json to {}\n{}'.format(fp, e.args))

def set_from_file(fp):
    """
    :type fp: str
    :returns: contents of file at file_path where each line is an element in returned set
    """
    try:
        if file_sys.file_exists(fp):
            with open(fp, 'r') as f:
                return set([line.strip() for line in f.readlines()])
        return set()
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(fp, e.args))

def str_from_file(fp):
    """
    :type fp: str
    :returns: contents of file at file_path as string
    """
    try:
        if file_sys.file_exists(fp):
            with open(fp, 'r') as f:
                return f.read()
        return str()
    except Exception as e:
        print('Error occured while reading {} as string\n{}'.format(fp, e.args))

def str_to_file(fp, content):
    """
    :type fp: str
    :type content: str
    """
    try:
        with open(fp, 'w') as f:
            f.write(content)
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(fp, e.args))
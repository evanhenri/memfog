import os
import json

from . import fs

def delete_file(file_path):
    """
    :type file_path: str
    """
    try:
        if fs.file_exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print('Error occured while deleting {}\n{}'.format(file_path, e.args))

def json_from_file(file_path):
    """
    :type file_path: str
    """
    try:
        if fs.file_exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return dict()
    except Exception as e:
        print('Error occured while reading {} as json\n{}'.format(file_path, e.args))

def json_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: json encodable obj
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(payload, f, indent=4)
        print('Saved {}'.format(file_path))
    except Exception as e:
        print('Error occured while writing json to {}\n{}'.format(file_path, e.args))

def set_from_file(file_path):
    """
    :type file_path: str
    :returns: contents of file at file_path where each line is an element in returned set
    """
    try:
        if fs.file_exists(file_path):
            with open(file_path, 'r') as f:
                return set([line.strip() for line in f.readlines()])
        return set()
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(file_path, e.args))

def str_from_file(file_path):
    """
    :type file_path: str
    :returns: contents of file at file_path as string
    """
    try:
        if fs.file_exists(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        return str()
    except Exception as e:
        print('Error occured while reading {} as string\n{}'.format(file_path, e.args))

def str_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: str
    """
    try:
        with open(file_path, 'w') as f:
            f.write(payload)
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(file_path, e.args))
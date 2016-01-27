import pickle
import json
import os

def json_from_file(file_path):
    """
    :type file_path: str
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print('Error occured while reading from {}\n{}'.format(file_path, e.args))

def json_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: json encodable obj
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(payload, f, indent=4)
        print('Successfully saved {}'.format(file_path))
    except Exception as e:
        print('Error occured while writing to {}\n{}'.format(file_path, e.args))

def pkl_from_file(file_path):
    """
    :type file_path: str
    """
    try:
        with open(file_path, 'rb') as in_stream:
            if os.path.getsize(file_path) > 0:
                print('loaded from' + file_path)
                return pickle.load(in_stream)
    except FileNotFoundError:
        print('{0} not found, creating new {0} file'.format(file_path))
    except Exception as e:
        print('Error occured while reading from {}\n{}'.format(file_path, e.args))

def pkl_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: Brain
    """
    try:
        with open(file_path, 'wb') as out_stream:
            pickle.dump(payload, out_stream, pickle.HIGHEST_PROTOCOL)
        print('Successfully saved {}'.format(file_path))
    except Exception as e:
        print('Error occured while writing to {}\n{}'.format(file_path, e.args))

def str_from_file(file_path):
    """
    :type file_path: str
    :retuers: contents of file at file_path as str
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print('Error occured while reading from {}\n{}'.format(file_path, e.args))

def str_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: str
    """
    try:
        with open(file_path, 'w') as f:
            f.write(payload)
        print('Export to {} successfull'.format(file_path))
    except Exception as e:
        print('Error occured while writing to {}\n{}'.format(file_path, e.args))
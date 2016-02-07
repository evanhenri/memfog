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

def mkfile(file_path):
    """
    :type file_path: str
    """
    try:
        open(file_path, 'w').close()
    except Exception as e:
        print('Error occured while making file {}\n{}'.format(file_path, e.args))

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
        print('{0} not found'.format(file_path))
    except Exception as e:
        print('Error occured while reading {} as pkl\n{}'.format(file_path, e.args))

def pkl_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: Brain
    """
    try:
        with open(file_path, 'wb') as out_stream:
            pickle.dump(payload, out_stream, pickle.HIGHEST_PROTOCOL)
        print('Saved {}'.format(file_path))
    except Exception as e:
        print('Error occured while writing pkl to {}\n{}'.format(file_path, e.args))

def set_from_file(file_path):
    """
    :type file_path: str
    :returns: contents of file at file_path where each line is an element in returned set
    """
    try:
        with open(file_path, 'r') as f:
            return set([line.strip() for line in f.readlines()])
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(file_path, e.args))

def seq_to_file(file_path, payload, delim='\n'):
    """
    :type file_path: str
    :type payload: str
    :type delim: str
    """
    delim_payload = delim.join(payload)
    try:
        with open(file_path, 'w') as f:
            f.writelines(delim_payload)
    except Exception as e:
        print('Error occured while writing sequence to {}\n{}'.format(file_path, e.args))

def str_from_file(file_path):
    """
    :type file_path: str
    :returns: contents of file at file_path as str
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
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
        print('Export to {} successfull'.format(file_path))
    except Exception as e:
        print('Error occured while writing string to {}\n{}'.format(file_path, e.args))
import pickle
import os

def pkl_from_file(file_path):
    """
    :type file_path: str
    """
    try:
        with open(file_path, 'rb') as in_stream:
            if os.path.getsize(file_path) > 0:
                return pickle.load(in_stream)
    except FileNotFoundError:
        print('{0} not found, creating new {0} file'.format(file_path))
    except Exception as e:
        print('Error occured while loading {}\n{}'.format(file_path, e.args))
    return

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
        print('Error occured while exporting to {}\n{}'.format(file_path, e.args))

def str_from_file(file_path):
    """
    :type file_path: str
    :retuers: contents of file at file_path as str
    """
    with open(file_path, 'r') as f:
        return f.read()

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
        print('Error occured while exporting to {}\n{}'.format(file_path, e.args))
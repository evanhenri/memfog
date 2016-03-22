import os
from collections import deque
from itertools import chain


def file_exists(fp):
    """
    :type fp: str
    Used to produce error notification if file_path is invalid
    """
    if os.path.isfile(fp):
        return True
    print('Invalid file path {}'.format(fp))
    return False

def init_dir(dp):
    """
    :type dp: str

    """
    try:
        if not os.path.isdir(dp):
            os.mkdir(dp)
    except Exception as e:
        print('Error occured while creating directory at {}\n{}'.format(dp, e.args))

def init_file(fp):
    """
    :type fp: str
    """
    try:
        if not os.path.isfile(fp):
            open(fp, 'w').close()
    except Exception as e:
        print('Error occured while making file {}\n{}'.format(fp, e.args))

def check_path(mode='r', *input_paths):
    """
    :type input_paths: list of strings
    :type mode: char
    Returns Trye/False depending on if using mode on input_path is valid
    """
    expanded_elements = map(os.path.expanduser, chain(input_paths))
    merged_elements = '/'.join(expanded_elements)
    split_elements = merged_elements.split('/')
    path_elements = deque(split_elements)
    partial_path = ''

    # iteratively reconstruct path until first instance when invalid path is found
    while len(path_elements) > 0:
        element = path_elements.popleft()
        tmp_path = partial_path + '/' + element
        if len(element) > 0:
            if os.path.isdir(tmp_path) or os.path.isfile(tmp_path):
                partial_path += '/' + element
            else:
                path_elements.appendleft(element)
                break

    if mode.startswith('r'):
        if os.path.isfile(partial_path) and os.access(partial_path, os.R_OK):
            return True
        return False

    if mode.startswith('w'):
        if os.access(partial_path, os.W_OK):
            # One item will exist in the deque if it is the file / dir name that is pending creation
            # If partial path already exists as a file, then it is possible to overwrite it
            if len(path_elements) == 1 or os.path.isfile(partial_path):
                return True
        return False

    if mode.startswith('a'):
        if os.path.isfile(partial_path) and os.access(partial_path, os.W_OK):
            return True
        return False

    if mode.startswith('x'):
        if os.path.isfile(partial_path) and os.access(partial_path, os.X_OK):
            return True
        return False




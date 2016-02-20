import os

def file_exists(file_path):
    """
    :type file_path: str
    Used to produce error notification if file_path is invalid
    """
    if os.path.isfile(file_path):
        return True
    print('Invalid file path {}'.format(file_path))
    return False

def init_dir(dir_path):
    """
    :type dir_path: str

    """
    try:
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)
    except Exception as e:
        print('Error occured while creating directory at {}\n{}'.format(dir_path, e.args))

def init_file(file_path):
    """
    :type file_path: str
    """
    try:
        if not os.path.isfile(file_path):
            open(file_path, 'w').close()
    except Exception as e:
        print('Error occured while making file {}\n{}'.format(file_path, e.args))

def validate_dir_path(input_path, default_dir_path):
    """
    :type input_path: str
    :type default_dir_path: str
    Attempts to resolve path to directory at input_path. Returns default_dir_path if unable to resolve
    """
    if input_path[-1] == '/':
        if os.path.isdir(input_path):
            return input_path
    if os.path.isdir(input_path + '/'):
        return input_path + '/'
    elif default_dir_path[-1] == '/':
        return default_dir_path
    return default_dir_path + '/'
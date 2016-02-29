import os

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

def validate_dir_path(input_dp, default_dp):
    """
    :type input_dp: str
    :type default_dp: str
    Attempts to resolve path to directory at input_path. Returns default_dir_path if unable to resolve
    """
    if input_dp[-1] == '/':
        if os.path.isdir(input_dp):
            return input_dp
    if os.path.isdir(input_dp + '/'):
        return input_dp + '/'
    elif default_dp[-1] == '/':
        return default_dp
    return default_dp + '/'
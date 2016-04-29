from . import util

def prompt_yn(msg=''):
    """
    :type msg: str
    :rtype: bool
    """
    return input('{} - y/n?\n> '.format(msg)).lower() == 'y'

def get_input():
    """
    :rtype: int or None
    """
    entry = input('> ')
    if util.is_valid_input(entry):
        return int(entry)
    return None

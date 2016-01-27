import readline

def confirm(msg=''):
    """
    :rtype: bool
    """
    return input('Confirm {} - y/n?\n> '.format(msg)).lower() == 'y'

def prefilled_input(prompt, prefill=''):
    """
    :type prompt: str
    :type prefill: str
    :returns: str from input prompt entry populated by default with editable text from prefill
    """
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()
from pathlib import Path


def get_path(*args):
    result = []

    for p in args:
        if not isinstance(p, Path):
            result.append(Path(p))
        else:
            result.append(p)
    return result

def init_dir(dp):
    """
    :type dp: pathlib.Path or str
    """
    dp = get_path(dp)[0]

    try:
        if not dp.is_dir():
            dp.mkdir()
    except Exception as e:
        print('Error occured while creating directory at {}\n{}'.format(str(dp), e.args))

def fix_path(p, default_dp, default_fn):
    """
    :param p: file path as str input from user
    :param default_dp: default directory path
    :param default_fn: default file name
    """
    p, default_dp, default_fn = get_path(p, default_dp, default_fn)
    p = p.expanduser()

    if p.parent.is_dir() and not p.exists():
        return p
    elif p.is_dir():
        return p / default_fn
    elif len(p.parts) == 1:
        return default_dp / p
    return default_dp / default_fn

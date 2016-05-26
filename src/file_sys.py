import os

class Path:
    def __init__(self, *path_pieces):
        self._pieces = [str(p) for p in path_pieces]

    def __str__(self):
        return os.path.expanduser(os.path.join(*self._pieces))

    def __add__(self, other):
        assert isinstance(other, Path)
        return Path(str(self), other)

    def append(self, piece):
        if isinstance(piece, str):
            self._pieces = os.path.join(self._pieces, piece)
        elif isinstance(piece, Path):
            self._pieces = os.path.join(self._pieces, str(piece))
        else:
            self._pieces = os.path.join(self._pieces, *piece)

    def exists(self):
        return os.path.exists(str(self))

    def is_dir(self):
        return os.path.isdir(str(self))

    def mkdir(self):
        os.mkdir(str(self))

    @property
    def parent(self):
        if len(self._pieces) > 1:
            return Path(self._pieces[:-1:])
        return Path('')

    @property
    def parts(self):
        return self._pieces

def init_dir(dp):
    """
    :type dp: pathlib.Path or str
    """
    dp = Path(dp)

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
    p = Path(p)
    default_dp = Path(default_dp)
    default_fn = Path(default_fn)

    if p.parent.is_dir() and not p.exists():
        return p
    elif p.is_dir():
        return p + default_fn
    elif len(p.parts) == 1:
        return default_dp + p
    return default_dp + default_fn

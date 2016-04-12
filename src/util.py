import string
import shlex

def k_intersect_v_diff(dict_a, dict_b):
    """
    :type dict_a: dict
    :type dict_b: dict
    :returns set containing keys found in both dicts if the value for that key is diffent between dicts
    """
    updated_keys = set()
    for k in dict_a.keys():
        if k in dict_b and dict_a[k] != dict_b[k]:
            updated_keys.add(k)
    return updated_keys

def is_valid_input(s):
    """
    :type s: str
    :rtype: bool
    """
    return len(s) > 0 and s.isdigit() and int(s) >= 0

def strip_punctuation(s):
    """
    :type s: str
    :returns: s stripped of all punctuation no found in exclusions
    """
    exclusions = ['\'','"']
    return ''.join([c for c in s if c not in string.punctuation or c in exclusions])

def standardize(s):
    """
    :type s: str
    :returns: list of non-empty words strings from s stripped of whitespace and punctuation
    """
    stripped = strip_punctuation(s).lower()
    return shlex.shlex(stripped)

class BidirectionCircularList(list):
    """
    built-in list() wrapper with circular next and prev functionality
    """
    def __init__(self, lst=[]):
        super(BidirectionCircularList, self).__init__(lst)
        self._index = 0

    def next(self):
        self._index += 1
        try:
            return self[self._index]
        except IndexError:
            self._index = 0
            return self[self._index]

    def prev(self):
        self._index -= 1
        try:
            return self[self._index]
        except IndexError:
            self._index = len(self)-1
            return self[self._index]




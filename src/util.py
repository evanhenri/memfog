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

class UniqueNeighborScrollList(list):
    """
    built-in list() wrapper with next and prev functionality
    Returns next/previous value from sequence or None if next/previous would go outside of sequence bounds
    Index used to track next/previous item begins after most recent item in list and resets each time a new item is added
    """
    def __init__(self, lst=[]):
        super(UniqueNeighborScrollList, self).__init__(lst)
        self._i = len(self)

    def append(self, p_object):
        # Do not append to self if current element equals previous element
        if len(self) == 0 or len(self) > 0 and self[-1] != p_object:
            super(UniqueNeighborScrollList, self).append(p_object)
        self.reset()

    def next(self):
        if self._i+1 >= len(self):
            return None
        self._i += 1
        return self[self._i]

    def prev(self):
        if self._i-1 < 0:
            return None
        self._i -= 1
        return self[self._i]

    def reset(self):
        self._i = len(self)




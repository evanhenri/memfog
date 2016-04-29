import string
import shlex
import itertools

def is_valid_input(s):
    return len(s) > 0 and s.isdigit() and int(s) >= 0

def strip_punctuation(s):
    """
    :returns: s stripped of all punctuation not found in exclusions
    """
    exclusions = ['\'','"']
    return ''.join([c for c in s if c not in string.punctuation or c in exclusions])

def standardize(s):
    """
    :returns: list of non-empty words strings from s stripped of whitespace and punctuation
    """
    stripped = strip_punctuation(s).lower()
    return shlex.shlex(stripped)

def unique_everseen(seq, key_func=None):
    """
    List unique elements, preserving order. Remember all elements ever seen.
    unique_everseen('AAAABBBCCDAABBB') --> A B C D
    unique_everseen('ABBCcAD', str.lower) --> A B C D
    """
    # tracks what items have already been encountered while iterating over seq
    seen = set()
    seen_add = seen.add
    if key_func is None:
        # for each item not currently in seen set
        for item in itertools.filterfalse(seen.__contains__, seq):
            # call cached function call
            seen_add(item)
            # return first instances of item
            yield item
    else:
        for item in seq:
            k = key_func(item)
            if k not in seen:
                seen_add(k)
                yield item

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




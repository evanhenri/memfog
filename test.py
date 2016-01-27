from fuzzywuzzy import fuzz
from fuzzywuzzy import process

s1 = "how to tie your shoes"
s2 = "how to shoe"

a = fuzz.partial_ratio(s1, s2)
b = fuzz.token_sort_ratio(s1, s2)
c = fuzz.token_set_ratio(s1, s2)

print(a, b, c)
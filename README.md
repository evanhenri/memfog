# memfog
Leave yourself healpful notes for later reference and find them again using fuzzy string searching

## Examples
```
# Add a memory that you may want to reference later
memfog.py -a

# add title
<Add a title> Without checking if key in dict, retrieve key value if present, otherwise add to dict 

# add keywords
<Add keywords> python dictionary dict add insert retrieve get "without checking" one liner

# add body
> dict_obj.setdefault(key, default value), get value for key is returned if key in dict
             otherwise key value pair added to dict and returned

# Lookup a stored memory by vague keywords
memfog.py dict get or insert without checking
0) [0%] How to fly
1) [4%] How to run
2) [72%] Without checking if key in dict, retrieve key value if present, otherwise add to dict
> 2

<body for memory 2 is show>
```
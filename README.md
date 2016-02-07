# memfog
Leave yourself healpful notes for later reference and find them again using fuzzy string searching

## Examples
```
# Add a memory that you may want to reference later
memfog.py -a
Title: <your title text>
Keywords: <keywords you think you would use search for current memory>
Body: <body text describing the memory you want to recall>

# Lookup a stored memory by vague keywords
memfog.py how to do <task> i did before but forgot how to do
0) [0%] How to fly
1) [4%] How to run
2) [72%] How to do <task>
> 2

The body for memory #2 is then displayed

Ctrl-C at any time to discard the memory if you decide not to save it 
```
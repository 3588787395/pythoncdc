# Source Generated with Decompyle++ (Python version)
# File: r5_03_comp_multifor.pyc (Python 3.11)

def mf_two_for(a, b):
    return [x + y for x in a for y in b]
def mf_three_for(a, b, c):
    return [x + y + z for x in a for y in b for z in c]
def mf_dependent(a):
    return [x * y for x in a for y in x]
def mf_dict_multi(a, b):
    return {x + y: x * y for x in a for y in b}
def mf_set_multi(a, b):
    return {x * y for x in a for y in b}
def mf_genexp_multi(a, b):
    return sum((x * y for x in a for y in b))

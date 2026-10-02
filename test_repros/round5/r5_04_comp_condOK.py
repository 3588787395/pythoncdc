# Source Generated with Decompyle++ (Python version)
# File: r5_04_comp_cond.pyc (Python 3.11)

def c_single_if(xs):
    return [x for x in xs if x > 0]
def c_double_if(xs):
    return [x for x in xs if x > 0 and x % 2 == 0]
def c_ifelse_body(xs):
    return [x if x > 0 else -x for x in xs]
def c_cross_for(a, b):
    return [x + y for x in a for y in b if x < y]
def c_between_fors(a, b, c):
    return [x + y + z for x in a for y in b for z in c]
def sc_cond_set(xs):
    return {x for x in xs if x >= 0}

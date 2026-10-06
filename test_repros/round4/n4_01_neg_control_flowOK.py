# Source Generated with Decompyle++ (Python version)
# File: n4_01_neg_control_flow.pyc (Python 3.11)

def n_for_else(xs):
    for x in xs:
        r = x
    r = 0
    return r
def n_while_else(n):
    i = 0
    while i < n:
        i += 1
    return i
def n_elif(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    else:
        return 'c'
def n_try_finally(x):
    try:
        r = x
    finally:
        r = x
    return r

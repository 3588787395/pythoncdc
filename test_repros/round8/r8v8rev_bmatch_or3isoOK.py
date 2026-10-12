# Source Generated with Decompyle++ (Python version)
# File: r8v8rev_bmatch_or3iso.pyc (Python 3.11)

def w1(x, g):
    r = 0
    match x:
        case 1 | 2 | 3 if x > 1:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r
def w2(x, g):
    r = 0
    match x:
        case 1 | 2:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r
def w3(x, g):
    r = 0
    match x:
        case 1 | 2 | 3:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r
def w4(x, g):
    r = 0
    match x:
        case 1 if g:
            r = 'one'
        case _:
            r = 'other'
    return r

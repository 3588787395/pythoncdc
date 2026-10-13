# Source Generated with Decompyle++ (Python version)
# File: r8v8rev3_bmatch_or4_battery.pyc (Python 3.11)

def v1(x, g):
    r = 0
    match x:
        case 1 | 2 | 3 | 4 if g:
            r = 'small'
        case 5 | 6:
            r = 'mid'
        case _:
            r = 'other'
    return r
def v2(x, g, h):
    r = 0
    match x:
        case 1 | 2 if g and h:
            r = 'both'
        case 3:
            r = 'three'
        case _:
            r = 'other'
    return r
def v3(x, g):
    r = 0
    match x:
        case 1 | 2 | 3 | 4 if x > 1:
            r = 'small'
        case _:
            r = 'other'
    return r

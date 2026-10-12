# Source Generated with Decompyle++ (Python version)
# File: r8v8rev_bmatch_v3.pyc (Python 3.11)

def v3(x, g, sink):
    r = 0
    match x:
        case 1 | 2 | 3:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r

# Source Generated with Decompyle++ (Python version)
# File: r8v8rev_bmatch_v1.pyc (Python 3.11)

def v1(x, g, sink):
    r = 0
    match x:
        case 1 if g:
            r = 1
            sink.append(r)
        case _:
            r = 2
    return r

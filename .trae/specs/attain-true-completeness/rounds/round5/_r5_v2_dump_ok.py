# Source Generated with Decompyle++ (Python version)
# File: rec1_b122b_r8v8rev_bmatch_guards_battery.pyc (Python 3.11)

def v1(x, g, sink):
    r = 0
    match x:
        case 1 if g:
            r = 1
            sink.append(r)
        case _:
            r = 2
    return r
def v2(x, y, g, sink):
    r = 0
    match x:
        case 1:
            match y:
                case 2 if g:
                    if g:
                        r = 21
                    else:
                        r = 22
                case _:
                    pass
        case _:
            r = 9
    return r
def v3(x, g, sink):
    r = 0
    match x:
        case 1 | 2 | 3 if g:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r
def v4(x, y, g):
    match x:
        case 7 if g:
            return 'seven'
        case _:
            return y

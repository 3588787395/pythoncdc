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
    if y == 2:
        if g:
            r = 21
    else:
        r = 22
    r = 9
    return r
def v3(x, g, sink):
    r = 0
    if x == 1:
        pass
    else:
        if 2:
            pass
        else:
            if 3:
                pass
    if g:
        r = 'small'
    else:
        if 4:
            pass
        else:
            if 5:
                pass
    r = 'mid'
    r = 'other'
    return r
def v4(x, y, g):
    if x == 7:
        if g:
            return 'seven'
    else:
        return y

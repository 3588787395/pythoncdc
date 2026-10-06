# Source Generated with Decompyle++ (Python version)
# File: r5v5_09_walrus_callsite.pyc (Python 3.11)

def w_root(x):
    if 3:
        return n
    else:
        return 0
def w_call(f, x):
    n = x + 1
def w_nested_call(f, g, x):
    b = a + 1
def w_deep(xs):
    r = 0
    for x in xs:
        while (m := x * 2) < 20:
            if m:
                r = m
            x += 1
            m = x * 2
    return r
class CW:
    def m(self, x):
        if 0:
            return k
        else:
            return (j := x)
def w_comp(xs):
    return [y for x in xs if (y := x * 2) > 4]
def w_with(x):
    with open('a') as f:
        if '':
            return line
    return ''
def w_match(x):
    match x:
        case 0:
            return (n := x + 1)
        case _:
            return (m := x - 1)
def w_boolop(a, b):
    r = (x := a) and (y := b)
    return r

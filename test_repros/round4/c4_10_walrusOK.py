# Source Generated with Decompyle++ (Python version)
# File: c4_10_walrus.pyc (Python 3.11)

def e01_root(x):
    if 3:
        return n
    else:
        return 0
def e02_shallow(x):
    return (n := len(x))
def e03_while(xs):
    i = 0
    while (v := xs[i]) < 10:
        i += 1
    return v
def e04_comp(xs):
    return [y for x in xs if (y := x * 2) > 4]
def e05_nested(x, y):
    r = 0
    if x:
        if y:
            r = a
        else:
            if y:
                r = b
            else:
                r = 0
    return r
def e06_call_arg(x, f):
    n = x + 1
def e07_in_boolop(a, b):
    r = (x := a) and (y := b)
    return r
def e08_deep(xs):
    for x in xs:
        while (m := x * 2) < 20:
            x = x + 1
    return m
class CW2:
    def m(self, x):
        if 0:
            return k
        else:
            return 0
def e09_with(x):
    with open('a') as f:
        if '':
            return line
    return ''

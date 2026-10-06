# Source Generated with Decompyle++ (Python version)
# File: r5v5_08_slice_callsite.pyc (Python 3.11)

def sl_root(s):
    return s[1:2]
def sl_nested(s):
    return s[1:2][0:1][::1]
def sl_call(s, g):
    return g(s[1:len(s) - 1:2], s[::-1])
def sl_deep(s, xs):
    r = 0
    for i in xs:
        if i:
            while i > 0:
                r = s[i:i + 2]
                i -= 1
    return r
class CSl:
    def m(self, s):
        with open('a') as f:
            return s[f.start:f.end:f.step]
            return None
def sl_comp(xs, n):
    return [x[n:] for x in xs]
def sl_target(xs):
    xs[1:3] = [0, 0]
    xs[:] = []
    del xs[::2]
    return xs
def sl_match(s, x):
    match x:
        case 0:
            return s[1:2]
        case _:
            return s[::2]

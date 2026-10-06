# Source Generated with Decompyle++ (Python version)
# File: c4_13_slice.pyc (Python 3.11)

def e01_root(s):
    return s[1:2]
def e02_shallow(s):
    return s[:]
def e03_step(s):
    return s[::2]
def e04_deep(s):
    if s:
        return s[1:len(s) - 1:2]
    else:
        return s[::-1]
def e05_tuple(s, t):
    return (s, t)[0][1:2]
def e06_target(xs):
    xs[1:3] = [0, 0]
    xs[:] = []
    del xs[::2]
    return xs
class CSL:
    def m(self, s):
        with open('a') as f:
            return s[f.start:f.end:f.step]
            return None
def e07_expr_bounds(s, a, b, c):
    return s[a + 1:b - 1:c * 2]
def e08_comp(xs, n):
    return [x[n:] for x in xs]
def e09_nested(s):
    return s[1:2][0:1][::1]

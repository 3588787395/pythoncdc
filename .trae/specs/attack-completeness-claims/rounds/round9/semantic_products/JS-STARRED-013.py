# Source Generated with Decompyle++ (Python version)
# File: c4_12_star_args.pyc (Python 3.11)

def e01_root(f, xs):
    return f(*xs)
def e02_shallow(f, x):
    return f(*x, 1)
def e03_mixed(f, xs):
    return f(1, *xs, 2, key=3)
def e04_deep(f, xs, ys):
    r = 0
    for i in range(2):
        if i:
            r = f(*xs, *ys, **({'k': i}))
    return r
def e05_defn(*args, **kwargs):
    return (args, kwargs)
def e06_nested(f, xs):
    def inner():
        return f(*xs, *xs)
    return inner()
class CSA:
    def m(self, f, xs):
        return f(*xs, self.v)
def e07_match_host(f, xs):
    if flag() == 0:
        r = f(*xs)
    else:
        if 1:
            r = f(*xs, 1)
    return r
def e08_kwstar(f, d):
    return f(**(d))
def e09_mixed_all(f, xs, d):
    return f(1, *xs, k=2, **(d))

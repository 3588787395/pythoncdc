# Source Generated with Decompyle++ (Python version)
# File: r5v5_07_starargs_callsite.pyc (Python 3.11)

def st_root(f, xs):
    return f(*(xs))
def st_nontail(f, xs):
    return f(1, *(xs))
def st_mixed(f, xs):
    return f(1, 2, k=3, *(xs))
def st_multistar(f, xs, ys):
    return f(*(ys), **({'k': 0}))
def st_deep(f, xs, ys):
    r = 0
    for i in range(2):
        if i:
            r = f(*(ys), **({'k': i}))
    return r
class CSt:
    def m(self, f, xs):
        for i in range(2):
            if i:
                return f(self.v, *(xs))
        return f(*(xs))
def st_close(f, xs):
    def inner():
        return f(*(xs))
    return inner()
def st_match(f, xs, x):
    match x:
        case 0:
            return f(*(xs))
        case _:
            return f(1, *(xs))
def st_comp(f, xs):
    return [v for v in xs]

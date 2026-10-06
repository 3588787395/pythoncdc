# Source Generated with Decompyle++ (Python version)
# File: c4_11_keyword_args.pyc (Python 3.11)

def e01_root(f):
    return f(1, 2, key=3, other=4)
def e02_shallow(f):
    return f(key=1)
def e03_deep(f):
    r = 0
    for i in range(3):
        if i:
            r = f(a=i, b=i + 1, c=i + 2)
    return r
def e04_dup_order(f):
    return f(b=1, a=2, **({'c': 3}))
def e05_mixed_pos(f):
    return f(1, 2, x=3, y=4)
class CKA:
    def m(self, f):
        return f(self.v, key=self.w)
def e06_match_host(f):
    if flag() == 0:
        r = f(a=1, b=2)
    else:
        r = f(a=0, b=0)
    return r
def e07_closure(f):
    def inner():
        return f(alpha=1, beta=2, gamma=3)
    return inner()
def e08_comp(f):
    return [f(v=v) for v in range(3)]
def e09_nested_call(f, g):
    return f(g(a=1), b=g(c=2), d=3)

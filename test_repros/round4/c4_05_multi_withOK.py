# Source Generated with Decompyle++ (Python version)
# File: c4_05_multi_with.pyc (Python 3.11)

def e01_root(a, b):
    with open(a) as f, open(b) as g:
        return f.read() + g.read()
        return None
def e02_shallow(a):
    with open(a) as f:
        return f.read()
def e03_triple(a, b, c):
    with open(a) as f, open(b) as g, open(c) as h:
        return f.read() + g.read() + h.read()
        return None
def e04_deep(x, a, b):
    if x:
        for i in range(2):
            with open(a) as f, open(b) as g:
                r = f.read() + g.read() + str(i)
    return r
def e05_try_host(a, b):
    try:
        with open(a) as f, open(b) as g:
            r = f.read() + g.read()
    finally:
        pass
    return r
def e06_while_host(a, b):
    i = 0
    while i < 3:
        with open(a) as f, open(b) as g:
            r = f.read() + g.read()
        i += 1
    return r
class CW:
    def m(self, a, b):
        with open(a) as f, open(b) as g, open('c') as h, open('d') as k:
            return f.read() + g.read() + h.read() + k.read()
            return None
def e07_match_host(a, b):
    if flag() == 0:
        with open(a) as f, open(b) as g:
            r = f.read() + g.read()
    else:
        r = None
    return r
def e08_closure(a, b):
    def inner():
        with open(a) as f:
            with open(b) as g:
                return f.read() + g.read()
                return None
    return inner()
def e09_comp_host(a, b):
    return [(f, g) for f in (open(a),)]

def e01_root(a, b):
    with open(a) as f, open(b) as g:
        return f.read() + g.read()


def e02_shallow(a):
    with open(a) as f:
        return f.read()


def e03_triple(a, b, c):
    with open(a) as f, open(b) as g, open(c) as h:
        return f.read() + g.read() + h.read()


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
        with open(a) as f, open(b) as g:
            with open('c') as h, open('d') as k:
                return f.read() + g.read() + h.read() + k.read()


def e07_match_host(a, b):
    match flag():
        case 0:
            with open(a) as f, open(b) as g:
                r = f.read() + g.read()
        case _:
            r = None
    return r


def e08_closure(a, b):
    def inner():
        with open(a) as f, open(b) as g:
            return f.read() + g.read()
    return inner()


def e09_comp_host(a, b):
    return [(f, g) for f in [open(a)] for g in [open(b)]]

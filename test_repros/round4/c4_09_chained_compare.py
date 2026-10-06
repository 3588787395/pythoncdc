def e01_root(a, b, c):
    return a < b < c


def e02_shallow(a, b):
    return a < b


def e03_mixed(a, b, c, d):
    if a < b <= c != d:
        return 1
    return 0


def e04_deep(xs):
    for x in xs:
        if 0 < x < 10 < x * 2:
            r = x
        else:
            r = 0
    return r


def e05_is_in(a, b, c):
    return a is b is not c


def e06_notin(a, b, c):
    return a in b not in c


def e07_comp(xs):
    return [x for x in xs if 0 < x < 100]


def e08_while(x):
    n = 0
    while 0 < x < n < 100:
        n += 1
    return n


class CCMP:
    def m(self, a, b, c):
        with open('a') as f:
            return a < b < c < len(f.read())


def e09_closure(a, b, c):
    def inner():
        return a < b < c
    return inner()

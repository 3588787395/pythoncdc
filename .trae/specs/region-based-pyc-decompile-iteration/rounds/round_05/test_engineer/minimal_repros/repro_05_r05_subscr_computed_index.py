def r05_subscr_computed_index(d, f):
    d[f()] = (r := make())
    return r
def f():
    return 0
def make():
    return 9

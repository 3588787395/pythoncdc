# Source Generated with Decompyle++ (Python version)
# File: c4_18_nested_comprehension.pyc (Python 3.11)

def e01_root(xs):
    return [[y for y in x] for x in xs]
def e02_shallow(xs):
    return [y for y in xs]
def e03_dict(xs, ys):
    return {x: [y for y in ys if y > x] for x in xs}
def e04_gen(xs):
    return list((y for x in xs for y in x))
def e05_deep_host(xs):
    r = None
    for x in xs:
        if x:
            r = {a: {b for b in x} for a in xs}
    return r
def e06_triple(xs):
    return [[[z for z in y] for y in x] for x in xs]
def e07_cond_nest(xs):
    return [y for x in xs if x for y in x if y]
class CNC:
    def m(self, xs):
        with open('a') as f:
            return [(x, f) for x in xs if x]
def e08_set(xs):
    return {frozenset((y for y in x)) for x in xs}
def e09_closure(xs):
    def inner():
        return {k: [v for v in x] for k, x in enumerate(xs)}
    return inner()

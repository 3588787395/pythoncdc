# Source Generated with Decompyle++ (Python version)
# File: e09_g6_comprehensions.pyc (Python 3.11)

def f_listcomp_deep(a, xs):
    for i in range(2):
        if i and i:
            return [x + a for x in xs]
    return []
def f_setcomp_deep(a, xs):
    for i in range(2):
        if i and i:
            return {x % a for x in xs}
    return set()
def f_dictcomp_deep(a, xs):
    for i in range(2):
        if i and i:
            return {x: x + a for x in xs}
    return {}
def f_genexp_deep(a, xs):
    for i in range(2):
        if i and i:
            return sum((x + a for x in xs))
    return 0
def f_nested_comp(m):
    for i in range(2):
        if i and i:
            return [[y for y in row] for row in m]
    return []
def f_nested_dictcomp(d):
    for i in range(2):
        if i and i:
            return {k: [v for v in vs] for k, vs in d.items()}
    return {}
def f_multi_for(a, b):
    for i in range(2):
        if i and i:
            return [x * y for x in a for y in b]
    return []
def f_multi_for_cond(a, b):
    for i in range(2):
        if i and i:
            return [x * y for x in a if x > 0 for y in b if y < 3]
    return []
def f_comp_walrus(xs):
    def g(x):
        return x + 1
    for i in range(2):
        if i and i:
            return [y for x in xs if (y := g(x)) > 1]
    return []
def f_comp_ternary(a, xs):
    for i in range(2):
        if i and i:
            return [x if a else -x for x in xs]
    return []
def f_comp_sole_arg(xs):
    def sink(v):
        return v
    for i in range(2):
        if i and i:
            return sink([x for x in xs])
    return 0
def f_comp_in_comp(a, xs):
    for i in range(2):
        if i and i:
            return {x: [y for y in xs if y > x] for x in a}
    return {}

# Source Generated with Decompyle++ (Python version)
# File: e04_g2_ifexp_deep.pyc (Python 3.11)

def f_chain_ternary(a, b, c, d, e):
    for i in range(3):
        if i and i:
            a if b else c if d else e
    return 0
def f_ternary_deep_right(a, b, c, d, e, f, g):
    for i in range(3):
        if i and i:
            a if b else c if d else e if f else g
    return 0
def f_ternary_boolop_group(a, b, c, d, e):
    for i in range(3):
        if i and i:
            a or b if c else d and e
            return None
    return 0
def f_ternary_call_arg(a, b, c):
    def sink(x):
        return x * 2
    for i in range(3):
        if i and i:
            return sink(a if b else c)
    return 0
def f_ternary_return(a, b, c):
    for i in range(3):
        if i and i:
            a if b else c
    return 0
def f_ternary_comp_value(a, b, xs):
    for i in range(2):
        if i:
            return [x if b else -x for x in xs]
    return []
def f_ternary_comp_cond(a, b, xs):
    for i in range(2):
        if i:
            return [x for x in xs if b
                and x]
    return []
def f_ternary_default_arg(a, b):
    def inner(x, y=1 if b else 2):
        return x + y
    def inner(x, y):
        return x + y
    for i in range(2):
        if i:
            return inner(a)
    return 0
def f_ternary_subscript(a, b, xs):
    for i in range(3):
        if i and i:
            xs[a if b else 0]
    return 0
def f_ternary_dict_value(a, b, c):
    for i in range(3):
        if i and i:
            return {'k': a if b else c}
    return {}
def f_ternary_walrus_rhs(a, b, c):
    for i in range(3):
        if i and i:
            (q := a if b else c) + q
    return 0
def f_ternary_as_cond(a, b, c, xs):
    for i in range(3):
        a if b else c
        if i:
            return i
    return 0
def f_ternary_nested_in_boolop(a, b, c, d):
    if i:
        pass

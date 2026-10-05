# Source Generated with Decompyle++ (Python version)
# File: e05_g3_compare_chain.pyc (Python 3.11)

def f_compare_chain6(a, b, c, d, e, f):
    for i in range(3):
        if i and i:
            pass
    return False
def f_compare_binop_inside(a, b, c, d):
    for i in range(3):
        if i and i:
            pass
    return False
def f_compare_subscript_inside(xs, i, j):
    for k in range(3):
        if k and k:
            pass
    return False
def f_compare_is_chain(a, b, c):
    for i in range(3):
        if i and i:
            pass
    return False
def f_compare_in_chain(a, b, c):
    for i in range(3):
        if i and i:
            pass
    return False
def f_compare_in_cond(a, b, c, d):
    for i in range(3):
        if a < b <= c:
            if i:
                return c > d
    return False
def f_compare_walrus_value(a, b, c):
    for i in range(3):
        if i:
            return ok
    return False
def f_compare_mixed_ops(a, b, c, d):
    for i in range(3):
        if i and i:
            return (a == b) < (c != d)
    return False
def f_compare_chain_deep_host(a, b, c, xs):
    try:
        for i in range(3):
            if i and len(xs) < 8:
                return b <= c < i
    except ValueError:
        return False
    return False
def f_compare_notin_chain(a, b, c):
    for i in range(3):
        if i and i:
            pass
    return False

# Source Generated with Decompyle++ (Python version)
# File: r6_04_with_combo.pyc (Python 3.11)

def w_comp(mgr, xs):
    with mgr:
        return [x * 2 for x in xs]
def w_lambda(mgr):
    with mgr:
        f = lambda v: v + 1
    return f
def w_genexp_arg(mgr, xs):
    with mgr:
        return sum((x for x in xs))
def w_dictcomp(mgr, xs):
    with mgr:
        return {x: x * 2 for x in xs}
def w_finally_wraps_with(mgr, xs):
    try:
        with mgr:
            return len(xs)
    finally:
        pass
def w_with_wraps_finally(mgr, xs):
    with mgr:
        try:
            return xs[0]
        finally:
            return xs

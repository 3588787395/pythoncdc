# Source Generated with Decompyle++ (Python version)
# File: n4_02_neg_expr.pyc (Python 3.11)

def n_multi_target(x):
    a = b = x
    return a + b
def n_augassign(x):
    y = x
    y += 1
    return y
def n_chain_compare(a, b, c):
    return a < b < c
def n_walrus(x):
    return (n := x)
def n_slice(s):
    return s[1:2]
def n_fstring(x):
    return f'{x!r}'
def n_kwarg(f):
    return f(a=1, b=2)
def n_star(f, xs):
    return f(*(xs))
def n_nested_comp(xs):
    return [[y for y in x] for x in xs]

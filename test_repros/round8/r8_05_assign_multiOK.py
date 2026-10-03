# Source Generated with Decompyle++ (Python version)
# File: r8_05_assign_multi.pyc (Python 3.11)

__doc__ = 'R8-05 Assign family: chained / multi-target / swap / star unpack (head-mid-tail) / nested unpack / attr / subscript / slice / chained subscript.'
def r8_assign_chain():
    a = b = c = 5
    a + b + c
    return a + b + c
def r8_assign_multi():
    a, b = 1, 2
    return a - b
def r8_assign_swap(a, b):
    a, b = (b, a)
    return (a, b)
def r8_assign_star_head(xs):
    a, *b = xs
    return (a, b)
def r8_assign_star_mid(xs):
    a, *m, c = xs
    return (a, m, c)
def r8_assign_star_tail(xs):
    *t, c = xs
    return (t, c)
def r8_assign_nested():
    a, (b, c) = 1, (2, 3)
    return (a, b, c)
def r8_assign_subscript_attr(xs, obj):
    xs[0] = obj.x
    obj.y = xs[1]
    return (xs, obj)
def r8_assign_slice(xs, ys):
    xs[1:3] = ys
    return xs
def r8_assign_chain_subscript(d1, d2, v):
    d1['k'] = d2['k'] = v
    (d1, d2)

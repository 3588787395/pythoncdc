# Source Generated with Decompyle++ (Python version)
# File: rv8_01_chain3_subscript.pyc (Python 3.11)

def chain3_subscript_rhs(xs, i, j):
    a = b = c = xs[i] + xs[j]
    return a + b + c
def chain3_all_subscript(m, v):
    m['x'] = m['y'] = m['z'] = v
    return m
def chain_mixed_targets(o, p, m, v):
    o.a = p.b = m['k'] = v
    return (o, p, m)
def chain_then_return_expr(xs, i):
    a = b = xs[i]
    return a * 2 + b
def chain_value_boolop(x, y):
    a = (x or y) and x and y
    return (a, b, c)
def single_assign_negctrl(q, w):
    q = w
    return q

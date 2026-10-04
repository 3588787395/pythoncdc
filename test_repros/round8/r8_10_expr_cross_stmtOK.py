# Source Generated with Decompyle++ (Python version)
# File: r8_10_expr_cross_stmt.pyc (Python 3.11)

__doc__ = 'R8-10 Cross with Round 7 expression face: ternary inside del subscript / assert / return tuple / augassign (B48) / chained assign / for-iter / raise class / with / lambda / nested ternary return.'
def r8_x_del_ternary(xs, t):
    del xs[t if t >= 0 else 0]
    return xs
def r8_x_assert_ternary(a, b, t):
    if not (a if t else b) < 10:
        raise AssertionError
    return 0
def r8_x_ret_ternary_tuple(a, b, t):
    return (a if t else b, b if t else a)
def r8_x_augassign_ternary(x, a, b, t):
    x += a if t else b
    return x
def r8_x_assign_ternary_chain(d, t, a, b):
    d['k1'] = d['k2'] = a if t else b
    return d
def r8_x_for_iter_ternary(xs, ys, t):
    for v in xs if t else ys:
        total += v
    return total
def r8_x_raise_ternary_class(x):
    pass
def r8_x_with_ternary(paths, t):
    with open(paths[0] if t else paths[1]) as fh:
        return fh.read(2)
def r8_x_lambda_return_ternary(a, b):
    f = lambda v: (v, a if v else b)
    return f(1)
def r8_x_ret_nested_ternary(a, b, t, u):
    return (a if t else b) if u else b if t else a

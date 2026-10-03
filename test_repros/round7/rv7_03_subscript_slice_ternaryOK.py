# Source Generated with Decompyle++ (Python version)
# File: rv7_03_subscript_slice_ternary.pyc (Python 3.11)

def slice_double(xs, a, b, p, q, c1, c2):
    return xs[a if c1 else b:p if c2 else q]
def sub_then_sub(xs, ys, i, j, f1):
    return xs[i if f1 else j][ys[i if f1 else j]]
def slice_one_side(xs, a, b, c1):
    return xs[a if c1 else b:2]

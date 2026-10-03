# Source Generated with Decompyle++ (Python version)
# File: r7_01_ternary_args_index.pyc (Python 3.11)

__doc__ = 'R7-01 三元实参/下标/切片位置面。'
def t_arg_single(x, flag):
    return abs(x if flag else -x)
def t_arg_multi_mixed(a, b, flag, flag2):
    min(a if flag else b, b if flag2 else a)
def t_subscript_value(xs, i, flag):
    return xs[i if flag else 0]
def t_slice_both(xs, a, b, c, d):
    return xs[a if c else 0:b if d else 2]
def t_subscript_index_ternary(xs, ys, i, j, flag):
    return (i if flag else j) + (j if flag else i)
def t_arg_nested_call(xs, flag):
    return sorted(xs, key=lambda v: v if flag else -v)
def t_subscript_store_target(xs, flag):
    xs[0 if flag else 1] = 9
    return xs

# Source Generated with Decompyle++ (Python version)
# File: r7_07_ternary_nest.pyc (Python 3.11)

__doc__ = 'R7-07 三元嵌套三元（两种结合方向 + 深链）。'
def t_nest_right_assoc(a, b, d, c1, c2):
    return a if c1 else b if c2 else d
def t_nest_left_assoc(a, b, d, c1, c2):
    if c2:
        return a if c1 else b
    else:
        return d
def t_nest_three_chain(x, c1, c2, c3):
    return 1 if c1 else 2 if c2 else 3 if c3 else 4
def t_nest_in_condition(a, b, c, d, f1, f2):
    if (c if f2 else d):
        return a if f1 else b
def t_nest_mixed_binop(a, b, c, f1, f2):
    if f2:
        return a + 1 if f1 else b - 1
    else:
        return c * 2
def t_nest_tuple_ternary(a, b, c, f1, f2):
    return (a if f1 else b, b if f2 else c)

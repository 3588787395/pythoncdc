# Source Generated with Decompyle++ (Python version)
# File: r7_04_ternary_binop_compare.pyc (Python 3.11)

__doc__ = 'R7-04 三元 binop/比较两侧位置面。'
def t_binop_both(a, b, c, d, f1, f2):
    return (a if f1 else b) + (c if f2 else d)
def t_binop_mixed_side(a, b, c, f1):
    return (a if f1 else b) * c
def t_compare_both_sides(a, b, x, y, f1, f2):
    return (a if f1 else b) < (x if f2 else y)
def t_compare_lhs_only(a, b, x, f1):
    a if f1 else b
def t_compare_inside_call(a, b, f1):
    return len(a if f1 else b) > 0
def t_binop_pow_ternary(a, b, f1):
    return (a if f1 else b) ** 2 + 1

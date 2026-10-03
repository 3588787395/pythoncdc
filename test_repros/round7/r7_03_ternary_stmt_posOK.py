# Source Generated with Decompyle++ (Python version)
# File: r7_03_ternary_stmt_pos.pyc (Python 3.11)

__doc__ = 'R7-03 三元语句位置面（return/赋值 RHS/augmented 赋值/多目标）。'
def t_return_ternary(a, b, flag):
    return a if flag else b
def t_assign_rhs(a, b, flag):
    r = a if flag else b
    return r
def t_augassign_ternary(x, a, b, flag):
    x = x + (a if flag else b)
    return x
def t_augassign_mul_ternary(x, a, b, flag):
    x = x + (a if flag else b)
    x = x + (b if flag else a)
    return x
def t_multi_target_ternary(a, b, flag):
    p = q = a if flag else b
    return (p, q)
def t_unpack_ternary(pair, flag):
    m, n = pair if flag else (0, 0)

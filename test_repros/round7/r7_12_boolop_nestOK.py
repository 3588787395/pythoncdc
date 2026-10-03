# Source Generated with Decompyle++ (Python version)
# File: r7_12_boolop_nest.pyc (Python 3.11)

__doc__ = 'R7-12 BoolOp 嵌套 BoolOp（≥3 层）+ 链式比较/三元内嵌。'
def b_nest_three_layers(a, b, c, d):
    return a and b and c
def b_nest_deep_right(a, b, c, d):
    return a and b or c and d
def b_nest_deep_mixed(a, b, c, d, e):
    return (a or b and c) and (d or e)
def b_nest_with_chain(a, b, c, d, e):
    return a < b and c < d < e
def b_nest_with_ternary(a, b, c, d, flag):
    return a and b if flag else c or d
def b_ternary_lhs_and(a, b, c, d, flag):
    if flag:
        return a
    else:
        return b and d
def b_nest_not_layers(a, b, c):
    return not (a or b and not c)

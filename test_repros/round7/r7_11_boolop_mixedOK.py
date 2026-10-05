# Source Generated with Decompyle++ (Python version)
# File: r7_11_boolop_mixed.pyc (Python 3.11)

__doc__ = 'R7-11 表达式面 BoolOp 混排（and/or/not 优先级）。'
def b_not_and_or(a, b, c):
    return a and not b or c
def b_not_group(a, b):
    return not (a and b)
def b_not_eq(a, b):
    return not a == b
def b_or_and_precedence(a, b, c, d):
    return a or b and c or d
def b_and_or_repeat(a, b, c):
    return a and b or b and c or a
def b_if_guard_not(a, b, c):
    if not a and b:
        return c
    return None

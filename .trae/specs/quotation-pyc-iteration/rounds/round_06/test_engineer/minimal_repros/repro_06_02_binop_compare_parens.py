"""Repro 06-02: Lost parens around Compare in low-precedence BinOp.

Defect: `(a >= b) & (c <= d)` becomes `a >= b & c <= d` which changes
semantics (BitAnd binds tighter than Compare in Python).

Root cause: BinOp/Compare emission does not wrap Compare operands in
parens when they appear as operands of a low-precedence binary op
(&, |, ^).
"""


def cond(a, b, c, d):
    return (a >= b) & (c <= d)


def cond2(a, b, c, d):
    return (a > b) | (c < d)


def cond3(a, b, c, d):
    return (a == b) ^ (c != d)

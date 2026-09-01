"""R15 DEFECT-REPRO: chained-compare + BoolOp OR with two variables in return.

`return A < x < B or C < y < D` — two distinct variables in each chained compare,
joined by OR. Exercises the same JUMP_IF_TRUE_OR_POP confusion with different
operands per compare arm.
"""
A = 1
B = 10
C = 20
D = 30


def f(x, y):
    return A < x < B or C < y < D

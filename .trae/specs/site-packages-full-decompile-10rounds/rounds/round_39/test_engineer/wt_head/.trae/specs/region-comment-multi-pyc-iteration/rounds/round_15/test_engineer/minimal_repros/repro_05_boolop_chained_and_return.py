"""R15 DEFECT-REPRO: chained-compare + BoolOp AND in return.

`return A < x < B and C < x < D` — chained compare joined by AND. Symmetric to
the OR variant; JUMP_IF_FALSE_OR_POP drives both the chained-compare and the
BoolOp AND short-circuit, exercising the same region-analysis confusion.
"""
A = 1
B = 10
C = 20
D = 30


def f(x):
    return A < x < B and C < x < D

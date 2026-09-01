"""R15 DEFECT-REPRO: three-way chained-compare + BoolOp OR in return.

`return A < x < B or C < x < D or E < x < F` — three chained compares joined
by OR, exercising multiple JUMP_IF_TRUE_OR_POP short-circuits in a return.
"""
A = 1
B = 10
C = 20
D = 30
E = 40
F = 50


def f(x):
    return A < x < B or C < x < D or E < x < F

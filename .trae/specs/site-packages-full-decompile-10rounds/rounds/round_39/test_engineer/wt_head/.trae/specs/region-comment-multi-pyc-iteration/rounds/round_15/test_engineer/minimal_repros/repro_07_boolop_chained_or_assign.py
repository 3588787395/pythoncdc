"""R15 DEFECT-REPRO: chained-compare + BoolOp OR assigned to variable.

`r = A < x < B or C < x < D; return r` — the BoolOp+chained-compare expression
is stored to a local then returned, exercising the pattern outside a direct
return context (Store + value-expression region).
"""
A = 1
B = 10
C = 20
D = 30


def f(x):
    r = A < x < B or C < x < D
    return r

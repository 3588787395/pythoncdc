"""R15 DEFECT-REPRO: minimal chained-compare + BoolOp OR in return.

Isolates the core pattern: `return A < x < B or C < x < D` with int constants,
removing datetime noise. JUMP_IF_FALSE_OR_POP (chained compare) interleaved with
JUMP_IF_TRUE_OR_POP (BoolOp OR) in a value/return context.
"""
A = 1
B = 10
C = 20
D = 30


def f(x):
    return A < x < B or C < x < D

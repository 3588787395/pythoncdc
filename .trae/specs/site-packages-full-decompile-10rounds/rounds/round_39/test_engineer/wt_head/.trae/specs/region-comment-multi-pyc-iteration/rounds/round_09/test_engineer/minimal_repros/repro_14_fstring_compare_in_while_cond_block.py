"""Repro 14: f-string with COMPARE_OP before while.

While-loop condition block has the same pre-statement extraction path.
Expected: all 3 segments preserved.
"""
def f(a, b):
    x = 'pre'
    s = f'{a!s}_{a != b!s}_end'
    while a > 0:
        a -= 1
    return s

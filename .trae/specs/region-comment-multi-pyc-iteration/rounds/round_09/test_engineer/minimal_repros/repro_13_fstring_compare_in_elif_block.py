"""Repro 13: f-string with COMPARE_OP before elif.

Same pattern but in an elif condition block. Expected: all 3 segments
preserved.
"""
def f(a, b):
    x = 'pre'
    if a == 1:
        return 'one'
    s = f'{a!s}_{a != b!s}_end'
    if a == 0:
        return s
    return x

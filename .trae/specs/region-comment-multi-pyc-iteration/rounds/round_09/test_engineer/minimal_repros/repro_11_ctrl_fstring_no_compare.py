"""Repro 11 (control): f-string without COMPARE_OP before if.

Verifies f-strings without COMPARE_OP are not affected. Expected: all 3
segments preserved.
"""
def f(a, b):
    x = 'pre'
    s = f'start_{a!s}_{b!s}_end'
    if a == 0:
        return s
    return x

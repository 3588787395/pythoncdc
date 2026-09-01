"""Repro 05: f-string with COMPARE_OP as the FIRST FormattedValue.

COMPARE_OP appears immediately after the first LOAD_CONST fragment.
Expected: all 3 segments preserved.
"""
def f(a, b):
    x = 'pre'
    s = f'{a != b!s}_mid_{a!s}_end'
    if a == 0:
        return s
    return x

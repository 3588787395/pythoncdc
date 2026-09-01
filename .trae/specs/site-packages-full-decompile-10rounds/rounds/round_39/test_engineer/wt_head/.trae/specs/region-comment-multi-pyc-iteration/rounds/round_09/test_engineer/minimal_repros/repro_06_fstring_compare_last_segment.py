"""Repro 06: f-string with COMPARE_OP as the LAST FormattedValue.

COMPARE_OP appears in the last FormattedValue before BUILD_STRING.
Expected: all 3 segments preserved.
"""
def f(a, b):
    x = 'pre'
    s = f'start_{a!s}_{a != b!s}'
    if a == 0:
        return s
    return x

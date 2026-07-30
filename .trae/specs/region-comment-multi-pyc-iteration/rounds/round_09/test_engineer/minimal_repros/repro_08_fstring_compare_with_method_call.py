"""Repro 08: f-string with COMPARE_OP and method call in FormattedValue.

COMPARE_OP combined with a method call (str.lower()) inside the same
FormattedValue. Expected: all 3 segments preserved.
"""
def f(a, b):
    x = 'pre'
    s = f'{a!s}_{str(a).lower() == b!s}_end'
    if a == 0:
        return s
    return x

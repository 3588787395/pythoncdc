"""Repro 12: f-string with chained compare (a < b < c) in FormattedValue.

Chained compare produces multiple COMPARE_OPs inside one FormattedValue.
Expected: all 3 segments preserved.
"""
def f(a, b, c):
    x = 'pre'
    s = f'{a!s}_{a < b < c!s}_end'
    if a == 0:
        return s
    return x

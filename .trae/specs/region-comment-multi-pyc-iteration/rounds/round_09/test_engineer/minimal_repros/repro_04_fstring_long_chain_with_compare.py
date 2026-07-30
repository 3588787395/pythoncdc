"""Repro 04: long f-string (many segments) with COMPARE_OP in the middle.

Mirrors backtest.pyc: 7+ segments with a COMPARE_OP FormattedValue in
the middle. The clearing heuristic truncates everything before the first
COMPARE_OP. Expected: all 7 segments preserved.
"""
def f(a, b, c, d, e, g):
    x = 'pre'
    s = f'start_{a!s}_mid_{b!s}_{c != d!s}_{e!s}_{g!s}_end'
    if a == 0:
        return s
    return x

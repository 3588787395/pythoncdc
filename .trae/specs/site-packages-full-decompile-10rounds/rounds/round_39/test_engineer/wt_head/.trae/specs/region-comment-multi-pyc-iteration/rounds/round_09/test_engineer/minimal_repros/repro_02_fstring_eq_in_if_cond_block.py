"""Repro 02: f-string with == in FormattedValue, before an if statement.

COMPARE_OP (==) inside f-string FormattedValue triggers the clearing
heuristic. Expected: all 3 segments preserved.
"""
def f(a, b):
    x = 'pre'
    user_code = f'val_{a!s}_{a == b!s}_end'
    if a == 0:
        return user_code
    return x

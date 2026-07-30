"""Repro 03: f-string with multiple COMPARE_OPs in separate FormattedValues.

Two COMPARE_OPs (!= and ==) inside the same f-string. The clearing
heuristic fires twice, truncating to only the tail. Expected: all 5
segments preserved.
"""
def f(a, b, c, d):
    x = 'pre'
    user_code = f'{a!s}_{a != b!s}_{c!s}_{c == d!s}_end'
    if a == 0:
        return user_code
    return x

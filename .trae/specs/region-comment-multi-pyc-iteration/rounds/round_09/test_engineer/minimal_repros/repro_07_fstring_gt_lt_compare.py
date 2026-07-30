"""Repro 07: f-string with > and < COMPARE_OPs.

Different COMPARE_OP variants (gt, lt) inside f-string. Expected: all 5
segments preserved.
"""
def f(a, b, c, d):
    x = 'pre'
    s = f'{a!s}_{a > b!s}_{c!s}_{c < d!s}_end'
    if a == 0:
        return s
    return x

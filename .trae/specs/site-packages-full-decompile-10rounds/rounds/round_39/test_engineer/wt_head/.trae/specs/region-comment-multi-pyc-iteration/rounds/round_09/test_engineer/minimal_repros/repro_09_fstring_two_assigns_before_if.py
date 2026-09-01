"""Repro 09: two f-string assignments before if, both with COMPARE_OP.

The first assignment's STORE sets pre_seen_store=True. The second
assignment's f-string is then truncated by the COMPARE_OP heuristic.
Expected: both assignments preserve their full f-strings.
"""
def f(a, b, c, d):
    s1 = f'{a!s}_{a != b!s}_end'
    s2 = f'{c!s}_{c != d!s}_end'
    if a == 0:
        return s1 + s2
    return ''

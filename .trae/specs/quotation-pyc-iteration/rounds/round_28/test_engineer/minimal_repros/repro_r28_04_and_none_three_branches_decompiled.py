# Source Generated with Decompyle++ (Python version)
# File: repro_r28_04_and_none_three_branches.pyc (Python 3.11)

def f(a, b, c, params):
    if a is not None and b is None:
        params['a'] = a
        return None
    elif a is None and c is not None:
        params['c'] = c
        return None
    elif b is not None and c is None:
        params['b'] = b
        return None

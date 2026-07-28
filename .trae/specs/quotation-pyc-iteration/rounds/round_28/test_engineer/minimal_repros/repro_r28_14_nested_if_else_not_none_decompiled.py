# Source Generated with Decompyle++ (Python version)
# File: repro_r28_14_nested_if_else_not_none.pyc (Python 3.11)

def f(a, b, params):
    if a is not None:
        if b is not None:
            params['x'] = 1
        else:
            params['x'] = 2
            return None
    elif b is not None:
        params['x'] = 3
        return None
    else:
        params['x'] = 4

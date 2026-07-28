# Source Generated with Decompyle++ (Python version)
# File: repro_r27_08_and_none_with_assign_body.pyc (Python 3.11)

def f(a, b, params):
    if a is not None and b is None:
        params['x'] = a
        return None
    elif a is None and b is not None:
        params['y'] = b
        return None
    elif a is not None and b is not None:
        params['x'] = a
        params['y'] = b
        return None

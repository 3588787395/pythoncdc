# Source Generated with Decompyle++ (Python version)
# File: pv9.pbpyc (Python 3.11)

def f(values):
    if len(values) > 3:
        raise ValueError('too many')
    elif len(values) == 1 and not isinstance(values[0], str):
        raise ValueError('first')
    elif len(values) >= 2 and not isinstance(values[1], str):
        raise ValueError('second')
    else:
        return None

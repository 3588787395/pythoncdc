# Source Generated with Decompyle++ (Python version)
# File: pb3.pbpyc (Python 3.11)

def f(values):
    if len(values) == 1 and not isinstance(values[0], str):
        raise ValueError('first')
    if len(values) >= 2 and not isinstance(values[1], str):
        raise ValueError('second')
    return str(*values)

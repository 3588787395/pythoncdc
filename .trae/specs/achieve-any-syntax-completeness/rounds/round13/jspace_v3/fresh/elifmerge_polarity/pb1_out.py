# Source Generated with Decompyle++ (Python version)
# File: pb1.pbpyc (Python 3.11)

def f(values):
    if len(values) > 3:
        raise ValueError('too many')
    elif len(values) == 1 and not isinstance(values[0], str):
        raise ValueError('first')
    elif len(values) >= 2 and not isinstance(values[1], str):
        raise ValueError('second')
    elif len(values) == 3 and not isinstance(values[2], str):
        raise ValueError('third')
    else:
        return str(*values)

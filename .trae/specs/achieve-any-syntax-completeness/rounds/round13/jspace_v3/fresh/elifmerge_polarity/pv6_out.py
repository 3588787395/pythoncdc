# Source Generated with Decompyle++ (Python version)
# File: pv6.pbpyc (Python 3.11)

def f(values):
    if len(values) > 4:
        raise ValueError('too many')
    elif len(values) == 1 and not isinstance(values[0], str):
        raise ValueError('first')
    elif len(values) >= 2 and not isinstance(values[1], str):
        raise ValueError('second')
    elif len(values) == 3 and not isinstance(values[2], str):
        raise ValueError('third')
    elif len(values) == 4 and not isinstance(values[3], str):
        raise ValueError('fourth')
    else:
        return str(*values)

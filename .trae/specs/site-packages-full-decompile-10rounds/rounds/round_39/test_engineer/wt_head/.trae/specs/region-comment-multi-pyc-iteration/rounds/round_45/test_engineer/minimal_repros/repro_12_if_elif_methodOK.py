# Source Generated with Decompyle++ (Python version)
# File: repro_12_if_elif_method.pyc (Python 3.11)

def func(x, freq):
    if freq[-1] == 'd':
        return x.isocalendar()
    elif freq[-1] == 'm':
        return x.month
    return x.year

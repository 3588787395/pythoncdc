# Source Generated with Decompyle++ (Python version)
# File: repro_06_full_combo.pyc (Python 3.11)

def f(a, b, *args, kw1, kw2='z', **kwargs):
    return (a, b, args, kw1, kw2, kwargs)
result = f(1, 2, 3, 4, kw1=5, extra=6)

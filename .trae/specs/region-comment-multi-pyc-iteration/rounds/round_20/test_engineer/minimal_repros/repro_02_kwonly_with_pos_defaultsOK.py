# Source Generated with Decompyle++ (Python version)
# File: repro_02_kwonly_with_pos_defaults.pyc (Python 3.11)

def f(a, b=1, *args, kw1='x', kw2=None):
    return (a, b, args, kw1, kw2)
result = f(10, kw1='y')

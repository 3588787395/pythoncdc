# Source Generated with Decompyle++ (Python version)
# File: repro_04_pos_and_kwonly.pyc (Python 3.11)

def f(a, *, kw1='x'):
    return a + kw1
result = f(1, kw1='z')

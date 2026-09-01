# Source Generated with Decompyle++ (Python version)
# File: repro_11_kwonly_in_if.pyc (Python 3.11)

def f(a, *, flag=True):
    if flag:
        return a
    else:
        return a + 1
result = f(1, flag=False)

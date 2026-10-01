# Source Generated with Decompyle++ (Python version)
# File: n2_01_try_simple.pyc (Python 3.11)

def f(d):
    try:
        return d['k']
        return None
    except KeyError:
        return 0

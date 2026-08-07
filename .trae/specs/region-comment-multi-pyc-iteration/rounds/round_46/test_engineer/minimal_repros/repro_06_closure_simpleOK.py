# Source Generated with Decompyle++ (Python version)
# File: repro_06_closure_simple.pyc (Python 3.11)

def outer(x):
    def inner():
        return x + 1
    return inner

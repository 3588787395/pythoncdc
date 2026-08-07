# Source Generated with Decompyle++ (Python version)
# File: repro_07_closure_multiple.pyc (Python 3.11)

def outer(a, b):
    def inner():
        return a + b
    return inner

# Source Generated with Decompyle++ (Python version)
# File: repro_r28_11_or_not_none_chain.pyc (Python 3.11)

def f(a, b):
    if a is None:
        if b is not None:
            return 1
        else:
            return 0

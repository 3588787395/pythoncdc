# Source Generated with Decompyle++ (Python version)
# File: cp_nonlocal_target.pyc (Python 3.11)

def outer():
    c = 0
    d = 1
    def inner():
        nonlocal c
        c += 1
    inner()

# Source Generated with Decompyle++ (Python version)
# File: cp_closure_capture.pyc (Python 3.11)

def outer():
    total = 0
    other = 5
    def inner():
        return total + other
    return inner

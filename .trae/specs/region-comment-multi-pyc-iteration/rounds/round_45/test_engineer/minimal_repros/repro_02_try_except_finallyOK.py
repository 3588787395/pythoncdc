# Source Generated with Decompyle++ (Python version)
# File: repro_02_try_except_finally.pyc (Python 3.11)

def func(x):
    try:
        result = x + 1
        return result
    except ValueError:
        cleanup = True
        return -1
    finally:
        cleanup = True

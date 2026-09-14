# Source Generated with Decompyle++ (Python version)
# File: c06_try_for_if_return.cpython-311.pyc (Python 3.11)

def f(items):
    try:
        for a in items:
            if a:
                return a
    except BaseException:
        return None

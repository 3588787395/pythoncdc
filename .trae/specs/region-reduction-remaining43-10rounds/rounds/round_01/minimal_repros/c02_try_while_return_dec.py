# Source Generated with Decompyle++ (Python version)
# File: c02_try_while_return.cpython-311.pyc (Python 3.11)

def f(items):
    try:
        if items:
            return items.pop()
        return None
    except BaseException:
        return None

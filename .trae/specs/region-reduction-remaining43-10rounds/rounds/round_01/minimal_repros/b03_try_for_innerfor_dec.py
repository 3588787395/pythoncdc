# Source Generated with Decompyle++ (Python version)
# File: b03_try_for_innerfor.cpython-311.pyc (Python 3.11)

def f(items):
    try:
        for a in items:
            for b in a:
                pass
    except BaseException:
        return None

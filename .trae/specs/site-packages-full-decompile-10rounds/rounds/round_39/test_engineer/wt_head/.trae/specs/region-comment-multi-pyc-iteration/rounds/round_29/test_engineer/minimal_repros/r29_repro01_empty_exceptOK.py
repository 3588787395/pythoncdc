# Source Generated with Decompyle++ (Python version)
# File: r29_repro01_empty_except.cpython-311.pyc (Python 3.11)

def func_empty_except():
    try:
        try:
            pass
        except:
            pass
        x = 1
    except:
        pass
    else:
        return x + y

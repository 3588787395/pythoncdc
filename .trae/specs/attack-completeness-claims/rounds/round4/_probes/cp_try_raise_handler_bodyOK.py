# Source Generated with Decompyle++ (Python version)
# File: cp_try_raise_handler_body.pyc (Python 3.11)

class E(Exception):
    pass
def f():
    try:
        raise E()
    except ValueError:
        return 1

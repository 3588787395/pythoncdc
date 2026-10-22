# Source Generated with Decompyle++ (Python version)
# File: cp_decorator_arg.pyc (Python 3.11)

def deco(tag):
    def wrap(f):
        return f
    return wrap
@deco('AB')
def g():
    return 1

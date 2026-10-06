# Source Generated with Decompyle++ (Python version)
# File: n5v5_03_fstring_deco_shallow.pyc (Python 3.11)

def deco(n):
    def wrap(f):
        return f
    return wrap
@deco(1)
def n_deco(x):
    return x
def n_fstring(x):
    return f'{x!r}'
def n_deco_class():
    @deco(2)
    class C:
        pass
    return C

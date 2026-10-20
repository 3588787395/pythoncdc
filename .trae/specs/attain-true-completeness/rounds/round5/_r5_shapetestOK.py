# Source Generated with Decompyle++ (Python version)
# File: _r5_shapetest.pyc (Python 3.11)

__doc__ = """Probe: how does the current decompiler render single-case matches
with post-match statements (no default)? Compiled with CPython 3.11.7."""
def f1(x):
    if x == 1:
        A()
    return 5
def f5(x):
    match x:
        case [a, b]:
            if a:
                R = b
        case _:
            return 5
def f6(x):
    if x == 1:
        A()
    y = 7
    return y
def g1(x):
    match x:
        case [a, b]:
            A(a, b)
        case _:
            B()
    return 5
def g2(x):
    match x:
        case [a, b]:
            A(a, b)
        case other:
            C(other)
    return 5
def g3(x):
    match x:
        case [a, b]:
            A(a, b)
        case 2:
            B()
    return 5

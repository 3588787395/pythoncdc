# Source Generated with Decompyle++ (Python version)
# File: _r5_shapetest2.pyc (Python 3.11)

__doc__ = 'More phantom-prone shapes: merge blocks after no-default matches.'
def f7(x):
    match x:
        case [a, b]:
            A(a, b)
        case _:
            y = 7
            return y
def f8(x):
    match x:
        case [a, b]:
            return a
        case _:
            y = 7
            return y
def f9(x):
    match x:
        case [a, b]:
            return a
def f10(x):
    match x:
        case [a, b]:
            if a:
                R = b
        case _:
            return 5

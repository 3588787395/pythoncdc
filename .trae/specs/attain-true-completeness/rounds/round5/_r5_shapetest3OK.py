# Source Generated with Decompyle++ (Python version)
# File: _r5_shapetest3.pyc (Python 3.11)

__doc__ = '[R5] B61 shape matrix: assert-in-body / or-guard / rest-capture / assert-in-default.'
def h1(x):
    match x:
        case int() as v if v < 1000:
            raise AssertionError
        case str() as s:
            return len(s)
def h2(x):
    match x:
        case int() as v if v > 10 or v < -10:
            pass
        case _:
            pass
    return v * 2
def h3(x):
    match x:
        case {'op': op, **rest}:
            del rest['tmp']
            return (op, rest)
        case [a, b]:
            return (a, b)
def h4(x):
    match x:
        case [a, b]:
            return (a, b)
        case _:
            if x is None:
                raise AssertionError
            else:
                raise TypeError('bad shape')

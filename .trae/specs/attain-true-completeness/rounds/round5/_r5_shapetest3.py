"""[R5] B61 shape matrix: assert-in-body / or-guard / rest-capture / assert-in-default."""


def h1(x):
    match x:
        case int() as v:
            assert v < 1000
            return v * 2
        case str() as s:
            return len(s)


def h2(x):
    match x:
        case int() as v if v > 10 or v < -10:
            return v * 2
        case _:
            pass
    return None


def h3(x):
    match x:
        case {"op": op, **rest}:
            del rest["tmp"]
            return op, rest
        case [a, b]:
            return a, b


def h4(x):
    match x:
        case [a, b]:
            return a, b
        case _:
            assert x is not None
            raise TypeError("bad shape")

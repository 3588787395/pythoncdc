"""[R11 repro_03] Pattern C2: 2-tuple unpack with mixed attr+name loads."""


def f(obj, v):
    if v:
        a, b = obj.x, v
        return a, b

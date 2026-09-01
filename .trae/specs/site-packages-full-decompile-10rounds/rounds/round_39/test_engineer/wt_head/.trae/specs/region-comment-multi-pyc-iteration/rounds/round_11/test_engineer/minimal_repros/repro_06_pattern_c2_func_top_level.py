"""[R11 repro_06] Pattern C2: 2-tuple unpack at function top level (no if)."""


def f(a, b):
    x, y = a, b
    return x + y

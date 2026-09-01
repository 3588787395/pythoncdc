"""[R11 repro_07] Pattern C2: 2-tuple unpack with subscript RHS."""


def f(d):
    if d:
        a, b = d['x'], d['y']
        return a, b

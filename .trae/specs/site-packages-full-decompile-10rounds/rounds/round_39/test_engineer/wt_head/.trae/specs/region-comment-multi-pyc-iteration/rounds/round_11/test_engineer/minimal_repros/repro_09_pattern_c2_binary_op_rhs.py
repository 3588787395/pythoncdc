"""[R11 repro_09] Pattern C2: 2-tuple unpack with binary-op RHS."""


def f(a, b):
    if a:
        x, y = a + 1, b * 2
        return x, y

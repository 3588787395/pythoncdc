"""[R11 repro_08] Pattern C2: 4-tuple unpack no-SWAP."""


def f(a, b, c, d):
    if a:
        w, x, y, z = a, b, c, d
        return w, x, y, z

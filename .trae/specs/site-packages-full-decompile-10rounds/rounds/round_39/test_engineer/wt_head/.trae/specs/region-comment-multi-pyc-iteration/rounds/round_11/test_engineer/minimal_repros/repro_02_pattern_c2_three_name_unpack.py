"""[R11 repro_02] Pattern C2: 3-tuple unpack no-SWAP."""


def f(a, b, c):
    if a:
        x, y, z = b, c, a
        return x, y, z

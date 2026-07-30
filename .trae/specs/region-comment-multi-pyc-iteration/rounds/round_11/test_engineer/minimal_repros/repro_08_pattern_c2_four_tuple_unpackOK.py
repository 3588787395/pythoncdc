# Source Generated with Decompyle++ (Python version)
# File: repro_08_pattern_c2_four_tuple_unpack.pyc (Python 3.11)

__doc__ = '[R11 repro_08] Pattern C2: 4-tuple unpack no-SWAP.'
def f(a, b, c, d):
    if a:
        w, x, y, z = (a, b, c, d)
        return (w, x, y, z)

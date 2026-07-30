# Source Generated with Decompyle++ (Python version)
# File: repro_02_pattern_c2_three_name_unpack.pyc (Python 3.11)

__doc__ = '[R11 repro_02] Pattern C2: 3-tuple unpack no-SWAP.'
def f(a, b, c):
    if a:
        x, y, z = (b, c, a)
        return (x, y, z)

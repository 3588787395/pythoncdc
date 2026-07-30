# Source Generated with Decompyle++ (Python version)
# File: repro_09_pattern_c2_binary_op_rhs.pyc (Python 3.11)

__doc__ = '[R11 repro_09] Pattern C2: 2-tuple unpack with binary-op RHS.'
def f(a, b):
    if a:
        x, y = (a + 1, b * 2)
        return (x, y)

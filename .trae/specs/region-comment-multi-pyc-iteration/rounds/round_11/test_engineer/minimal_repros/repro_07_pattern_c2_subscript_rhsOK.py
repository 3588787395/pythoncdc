# Source Generated with Decompyle++ (Python version)
# File: repro_07_pattern_c2_subscript_rhs.pyc (Python 3.11)

__doc__ = '[R11 repro_07] Pattern C2: 2-tuple unpack with subscript RHS.'
def f(d):
    if d:
        a, b = (d['x'], d['y'])
        return (a, b)

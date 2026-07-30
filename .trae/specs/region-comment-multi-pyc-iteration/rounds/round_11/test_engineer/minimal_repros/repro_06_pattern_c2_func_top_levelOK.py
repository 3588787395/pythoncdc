# Source Generated with Decompyle++ (Python version)
# File: repro_06_pattern_c2_func_top_level.pyc (Python 3.11)

__doc__ = '[R11 repro_06] Pattern C2: 2-tuple unpack at function top level (no if).'
def f(a, b):
    x, y = (a, b)
    return x + y

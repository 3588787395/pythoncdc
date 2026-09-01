# Source Generated with Decompyle++ (Python version)
# File: repro_03_pattern_c2_attr_and_name.pyc (Python 3.11)

__doc__ = '[R11 repro_03] Pattern C2: 2-tuple unpack with mixed attr+name loads.'
def f(obj, v):
    if v:
        a, b = (obj.x, v)
        return (a, b)

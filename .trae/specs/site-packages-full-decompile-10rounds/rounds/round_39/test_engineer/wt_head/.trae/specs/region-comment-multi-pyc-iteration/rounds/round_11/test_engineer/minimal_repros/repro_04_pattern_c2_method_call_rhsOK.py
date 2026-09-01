# Source Generated with Decompyle++ (Python version)
# File: repro_04_pattern_c2_method_call_rhs.pyc (Python 3.11)

__doc__ = '[R11 repro_04] Pattern C2: 2-tuple unpack with method-call RHS.'
def f(obj):
    if obj.flag:
        a, b = (obj.get_a(), obj.get_b())
        return (a, b)

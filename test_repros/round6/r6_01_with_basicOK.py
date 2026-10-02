# Source Generated with Decompyle++ (Python version)
# File: r6_01_with_basic.pyc (Python 3.11)

def w_no_as(mgr):
    with mgr:
        return 1
def w_as_single(mgr):
    with mgr as f:
        return f
def w_two_mixed(m1, m2):
    with m1 as a, m2:
        return a
def w_three(m1, m2, m3):
    with m1 as a, m2 as b, m3 as c:
        return a + b + c
def w_tuple_unpack(mgr):
    with mgr as (a, b):
        return a + b
def w_star_unpack(mgr):
    with mgr:
        a, *rest = None
        return a + rest[0]
def w_subscript_mgr(mgrs):
    with mgrs[0] as v:
        return v

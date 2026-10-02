def mk(v):
    return v


def w_call_mgr(a, b):
    with mk(a) as f, mk(b) as g:
        return f + g


def w_attr_mgr(mgr):
    with mgr.inner as v:
        return v


def w_deep_unpack(mgr):
    with mgr as (a, (b, c)):
        return a + b + c


def w_star_mid(mgr):
    with mgr as (a, *rest, b):
        return a + b + rest[0]


def w_two_noas(m1, m2):
    with m1, m2:
        return 2


def w_ternary_mgr(m1, m2, v):
    with (m1 if v else m2) as x:
        return x

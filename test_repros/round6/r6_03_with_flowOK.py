# Source Generated with Decompyle++ (Python version)
# File: r6_03_with_flow.pyc (Python 3.11)

def w_return(mgr, v):
    with mgr:
        return v
        return None
def w_break(mgr, xs):
    with mgr:
        for x in xs:
            if x > 2:
                break
        return x
        return None
def w_continue(mgr, xs):
    total = 0
    with mgr:
        for x in xs:
            if x % 2:
                continue
            total += x
            continue
    return total
def w_raise(mgr, v):
    with mgr:
        raise ValueError(v)
def w_return_in_nest(m1, m2, v):
    with m1, m2:
        return v
        return None
def w_early_return(mgr, v):
    with mgr as x:
        if v > 0:
            return x
        else:
            x = v
    return x

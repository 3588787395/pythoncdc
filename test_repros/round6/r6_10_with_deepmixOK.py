# Source Generated with Decompyle++ (Python version)
# File: r6_10_with_deepmix.pyc (Python 3.11)

def w_loop_nest_with(mgr, xs):
    with mgr:
        for x in xs:
            with mgr as y:
                if y:
                    return x
    return None
def w_break_in_with(mgr, xs):
    with mgr:
        for x in xs:
            if x:
                break
        else:
            return -1
    return 0
def w_assign_after_with(mgr, xs):
    with mgr:
        out = list(xs)
    return out
def w_while_in_with(mgr, n):
    with mgr:
        while n > 0:
            n -= 1
            if n == 2:
                break
    return n
def w_nested_flow(m1, m2, xs):
    with m1:
        for x in xs:
            with m2:
                if x > 3:
                    continue
                elif x < 0:
                    break
        return x

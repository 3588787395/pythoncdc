def w_return(mgr, v):
    with mgr:
        return v


def w_break(mgr, xs):
    with mgr:
        for x in xs:
            if x > 2:
                break
        return x


def w_continue(mgr, xs):
    total = 0
    with mgr:
        for x in xs:
            if x % 2:
                continue
            total += x
    return total


def w_raise(mgr, v):
    with mgr:
        raise ValueError(v)


def w_return_in_nest(m1, m2, v):
    with m1:
        with m2:
            return v


def w_early_return(mgr, v):
    with mgr as x:
        if v > 0:
            return x
        x = v
    return x

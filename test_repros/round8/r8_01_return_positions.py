"""R8-01 Return position forms: branches / nested / loop / try-finally / generator / lambda / unpack."""


def r8_ret_multi_branch(x):
    if x > 0:
        return "pos"
    elif x == 0:
        return "zero"
    else:
        return "neg"


def r8_ret_nested_if(x, y):
    if x > 0:
        if y > 0:
            return "both"
        return "x_only"
    return "none"


def r8_ret_in_loop(xs):
    for x in xs:
        if x < 0:
            return x
    else:
        return -1
    return None


def r8_ret_try_except(xs, i):
    try:
        v = xs[i]
        return v
    except IndexError:
        return "oops"
    finally:
        pass


def r8_ret_finally_overwrite(xs, i):
    r = "init"
    try:
        r = xs[i]
        return r
    finally:
        r = "fin"


def r8_ret_gen(n):
    yield 1
    yield 2
    return "done"


def r8_ret_tuple(a, b):
    return a, b


def r8_ret_star(xs, a):
    return a, *xs


def r8_ret_lambda_implicit(x):
    g = lambda v: v + x
    return g(3)

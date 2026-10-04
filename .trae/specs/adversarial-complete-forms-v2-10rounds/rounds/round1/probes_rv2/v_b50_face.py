"""rv2 变体面 B50（r7_08 t_host_try_sections 邻域）：双 except / 无 finally / 纯赋值"""

def v_two_except_fin(xs, i, flag):
    try:
        r = xs[i] if flag else xs[0]
    except IndexError:
        r = -1 if flag else -2
    except KeyError:
        r = -3 if flag else -4
    finally:
        r = r if flag else 0
    return r


def n_plain_assign_fin(xs, i, flag):
    try:
        r = xs[i]
    except IndexError:
        r = -1
    finally:
        r = r if flag else 0
    return r


def n_ternary_nofin(xs, i, flag):
    try:
        r = xs[i] if flag else xs[0]
    except IndexError:
        r = -1 if flag else -2
    return r

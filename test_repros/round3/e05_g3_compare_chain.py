# e05: Compare 链——6 级链/链中嵌 BinOp/Subscript/is-in-notin 冷门叶/条件位/海象值
def f_compare_chain6(a, b, c, d, e, f):
    for i in range(3):
        if i:
            while i:
                return a < b <= c < d <= e < f
    return False


def f_compare_binop_inside(a, b, c, d):
    for i in range(3):
        if i:
            while i:
                return a + 1 < b * 2 <= c - d
    return False


def f_compare_subscript_inside(xs, i, j):
    for k in range(3):
        if k:
            while k:
                return xs[0] < xs[i + 1] <= xs[j]
    return False


def f_compare_is_chain(a, b, c):
    for i in range(3):
        if i:
            while i:
                return a is b is not c
    return False


def f_compare_in_chain(a, b, c):
    for i in range(3):
        if i:
            while i:
                return a in b not in c
    return False


def f_compare_in_cond(a, b, c, d):
    for i in range(3):
        if a < b <= c:
            while i:
                return c > d
    return False


def f_compare_walrus_value(a, b, c):
    for i in range(3):
        if i:
            if (ok := a < b <= c):
                return ok
    return False


def f_compare_mixed_ops(a, b, c, d):
    for i in range(3):
        if i:
            while i:
                return (a == b) < (c != d)
    return False


def f_compare_chain_deep_host(a, b, c, xs):
    try:
        for i in range(3):
            if i:
                while len(xs) < 8:
                    return b <= c < i
    except ValueError:
        return False
    return False


def f_compare_notin_chain(a, b, c):
    for i in range(3):
        if i:
            while i:
                return a not in b in c
    return False

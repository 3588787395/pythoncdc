"""r3v3-C 反向外推 + 收缩 + 非 boolop 误伤面——位 1 B98 tail-value 守卫攻击。"""


def g_or_in_and_left(a, b, c):
    return (a or b) and c


def g_and_or_right(a, b, c):
    return a and (b or c)


def g_and_or_and(a, b, c, d):
    return a and (b or c) and d


def g_or_pair_and_or_pair(a, b, c, d):
    return (a or b) and (c or d)


def g_or_and_plain(a, b, c):
    return a or (b and c)


def g_nested_parens(a, b, c, d, e):
    return ((a or b) and (c or d)) and e


def g_mixed_value_group(a, b, c, d):
    return (a and b) or c and d


def g_shrink_and(a, b, c):
    return (a or b) and c


def g_shrink_or(a, b, c):
    return (a and b) or c


def g_shrink_pair(a, b, c, d):
    return (a or b) and (c or d)


def g_plain_flat(a, b, c):
    return a or b and c


def g_in_while(a, b, c):
    r = []
    while a:
        r.append((b or c) and a)
        break
    return r


def g_nonbool_if_nested(a, b):
    if a:
        if b:
            return 1
        return 2
    return 3


def g_nonbool_if_chain(a, b, c):
    if a:
        return 1
    if b:
        return 2
    if c:
        return 3
    return 4

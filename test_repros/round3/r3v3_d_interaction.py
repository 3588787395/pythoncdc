"""r3v3-D 位 1 × 位 2 交互——for/while 宿主 + boolop 分组同时触发面。"""


def i_for_return_group(y, a, b, c):
    for i in y:
        return (a or b) and c
    return 0


def i_for_if_return_group(y, a, b, c):
    for i in y:
        if i:
            return (a or b) and c
    return 0


def i_while_if_return_group(n, a, b, c):
    while n < 3:
        if n:
            return (a and b) or c
        n += 1
    return 0


def i_for_return_flat_or(y, a, b, c):
    for i in y:
        return a or b or c
    return 0


def i_for_return_group_pair(y, a, b, c, d):
    for i in y:
        return (a or b) and (c or d)
    return 0


def i_for_return_chain_compare(y, a, b, c):
    for i in y:
        return a < b < c
    return False


def i_for_return_group_and_chain(y, a, b, c, d):
    for i in y:
        return (a or b) and (c < d)
    return 0


def i_while_group_value(n, a, b, c):
    acc = []
    while n < 3:
        acc.append((a or b) and c)
        n += 1
    return acc

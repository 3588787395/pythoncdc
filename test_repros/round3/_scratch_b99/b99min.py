def for_noif(a, b, c, y):
    for i in y:
        return a or b or c
    return 0


def for_host_plain(a, b, c, y):
    for i in y:
        if i:
            return a or b or c
    return 0


def w_host(a, b, c):
    n = 0
    while n < 3:
        if n:
            return a or b or c
        n += 1
    return 0


def top(a, b, c):
    return a or b or c


def if_top(a, b, c, flag):
    if flag:
        return a or b or c
    return 0


def for_flat_and(a, b, c, y):
    for i in y:
        if i:
            return a and b and c
    return 0


def for_grouped(a, b, c, y):
    for i in y:
        if i:
            return (a or b) and c
    return 0


def while_noif(a, b, c):
    n = 0
    while n < 3:
        return a or b or c
    return 0

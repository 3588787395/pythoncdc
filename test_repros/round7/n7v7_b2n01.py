def n2a(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            continue
        acc += x
    return acc


def n2b(n, flag):
    s = 0
    while n > 0:
        n -= 1
        if n % 2:
            continue
        s += n
    return s

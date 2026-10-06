def n3a(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += x
        acc += 1
    return acc


def n3b(n, flag):
    s = 0
    while n > 0:
        if n > 5:
            if n % 2 == 0:
                s += n
            else:
                s += 1
        n -= 1
    return s

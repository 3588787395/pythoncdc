def n2c(xs, flag):
    acc = 0
    for x in xs:
        if x < 0:
            acc -= 1
            continue
        acc += x
    else:
        acc += 1000
    return acc


def n2d(xs, k):
    n = 0
    for x in xs:
        if x == k:
            continue
        else:
            n += 1
    return n

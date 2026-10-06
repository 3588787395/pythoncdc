def n4c(xs, k):
    try:
        i = xs.index(k)
    except ValueError:
        return -1
    return i


def n4d(xs, flag):
    total = 0
    for x in xs:
        total += x
    return total

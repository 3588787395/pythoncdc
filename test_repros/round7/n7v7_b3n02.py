def n3c(xs, k):
    for x in xs:
        if x == k:
            break
    else:
        return -1
    return 1


def n3d(n, k):
    while n > 0:
        if n == k:
            break
        n -= 1
    else:
        return -1
    return 1

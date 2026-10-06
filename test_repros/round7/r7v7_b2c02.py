def b2c02_shallow(xs, k):
    n = 0
    for x in xs:
        if x == k:
            continue
        else:
            continue
    return n


def b2c02_deep(xs, k, flag):
    n = 0
    for x in xs:
        if flag:
            if x > 0:
                if x == k:
                    continue
                else:
                    continue
            n += 1
    return n

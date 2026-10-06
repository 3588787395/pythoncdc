def b3c02_shallow(xs, k):
    acc = 0
    for x in xs:
        if x == k:
            continue
        acc += x
    else:
        acc += 1000
    return acc


def b3c02_deep(xs, k, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x == k:
                    continue
            acc += x
        else:
            acc -= 1
    else:
        acc += 1000
    return acc

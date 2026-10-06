def b2c03_shallow(xs, k):
    acc = 0
    for x in xs:
        if x == k:
            continue
        else:
            break
    return acc


def b2c03_deep(xs, k, flag):
    acc = 0
    while xs:
        if flag:
            if acc >= 0:
                if xs[0] == k:
                    continue
                else:
                    break
        acc += 1
        xs = xs[1:]
    return acc

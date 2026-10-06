def b4c03_shallow(xs, k):
    acc = 0
    for x in xs:
        if x > 0:
            if x == k:
                acc = -1
                break
            acc += x
        else:
            acc -= 1
    else:
        acc += 100
    return acc


def b4c03_deep(xs, k, flag):
    acc = 0
    if flag:
        for x in xs:
            if x > 0:
                if x == k:
                    acc = -1
                    break
                if x > 10:
                    acc += 10
                else:
                    acc += x
            else:
                acc -= 1
        else:
            acc += 100
    return acc

def b3c03_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            if flag:
                acc += x
            acc += 1
        acc += 2
    return acc


def b3c03_deep(xs, flag):
    acc = 0
    for x in xs:
        if x != 0:
            if x > 0:
                if flag:
                    if x > 10:
                        acc += 10
                    else:
                        acc += x
                acc += 1
            acc += 2
        acc += 3
    return acc

def b2c01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x % 2 == 0:
            if flag:
                continue
        acc += x
        acc += 1
    return acc


def b2c01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x % 2 == 0:
                    if flag:
                        continue
                acc += x
        acc += 1
        acc += acc > 1000
    return acc

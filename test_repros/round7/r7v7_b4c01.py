def b4c01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            if flag:
                acc += x
            else:
                acc -= x
        acc += 1
    return acc


def b4c01_deep(xs, flag):
    acc = 0
    for x in xs:
        if x != 0:
            if x > 0:
                if flag:
                    if x > 100:
                        acc += 100
                    else:
                        acc += x
                else:
                    acc -= x
        acc += 1
    return acc

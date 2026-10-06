def b2b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 9:
            break
        acc += x
    return acc


def b2b01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if acc > 0:
                if x > 9:
                    break
                acc += 1
        acc += x
    return acc

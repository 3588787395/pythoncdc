def b3b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x < 0:
            continue
        acc += x
    return acc


def b3b01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if acc >= 0:
                if x < 0:
                    continue
                acc += x
        else:
            acc -= 1
    return acc

def b2b04_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += x
        else:
            continue
        acc += 1
    return acc


def b2b04_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x > 100:
                    acc -= x
                else:
                    acc += x
            else:
                continue
        else:
            acc += 2
        acc += 1
    return acc

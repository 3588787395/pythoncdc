def b2a01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 3:
            continue
        acc += x
    return acc


def b2a01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 1:
                if x > 2:
                    if x > 3:
                        continue
                    acc -= 1
                acc += 2
            acc += 3
        acc += x
    return acc

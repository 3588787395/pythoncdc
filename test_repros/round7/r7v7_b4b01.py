def b4b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += 1
        else:
            acc -= 1
    return acc


def b4b01_deep(xs, flag):
    acc = 0
    if flag:
        for x in xs:
            if x > 0:
                if x > 10:
                    if x > 100:
                        acc += 3
                    else:
                        acc += 2
                else:
                    acc += 1
            else:
                if x < -10:
                    acc -= 3
                else:
                    acc -= 1
    return acc

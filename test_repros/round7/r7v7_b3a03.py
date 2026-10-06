def b3a03_shallow(xs, flag):
    acc = 0
    try:
        for x in xs:
            if x > 0:
                acc += x
            acc += 1
    except TypeError:
        acc = -1
    return acc


def b3a03_deep(xs, flag):
    acc = 0
    try:
        if flag:
            for x in xs:
                if x > 0:
                    if x > 100:
                        acc += 10
                    else:
                        acc += x
                acc += 1
    except TypeError:
        acc = -1
    return acc

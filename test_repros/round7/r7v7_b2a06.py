def b2a06_shallow(xs, ys, flag):
    acc = 0
    for x in xs:
        if x == 0:
            continue
        for y in ys:
            if y == 0:
                continue
            acc += x * y
    return acc


def b2a06_deep(xs, ys, flag):
    acc = 0
    for x in xs:
        if flag:
            if x == 0:
                continue
            for y in ys:
                if flag and y == 0:
                    continue
                if y < 0:
                    if y == -1:
                        continue
                    acc += x
                acc += x * y
    return acc

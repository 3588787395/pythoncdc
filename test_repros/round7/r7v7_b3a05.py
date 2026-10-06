def b3a05_shallow(xs, ys, flag):
    acc = 0
    for x in xs:
        if x > 0:
            for y in ys:
                if y > 0:
                    acc += x * y
                acc += y
        acc += x
    return acc


def b3a05_deep(xs, ys, flag):
    acc = 0
    for x in xs:
        if flag:
            if x != 0:
                for y in ys:
                    if flag:
                        if y != 0:
                            if y > 0:
                                acc += x * y
                            acc += y
                acc += x
        acc += 1
    return acc

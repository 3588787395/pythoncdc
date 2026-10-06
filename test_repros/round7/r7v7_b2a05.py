def b2a05_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 5:
            acc -= 1
            continue
        acc += x
    return acc


def b2a05_deep(xs, flag):
    acc = 0
    while xs:
        if flag:
            if acc > 0:
                if len(xs) > 5:
                    acc -= 1
                    continue
                acc += 1
        xs = xs[1:]
    return acc

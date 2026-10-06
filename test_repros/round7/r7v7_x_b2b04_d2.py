def x_b2b04_d2(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                acc += x
            else:
                continue
        acc += 1
    return acc

def x_b4c03_d2(xs, k):
    acc = 0
    for x in xs:
        if x > 0:
            if x == k:
                acc = -1
                break
            if x > 10:
                acc += 10
            else:
                acc += x
        else:
            acc -= 1
    else:
        acc += 100
    return acc

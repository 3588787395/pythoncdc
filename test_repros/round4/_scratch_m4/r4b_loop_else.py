def f(xs):
    while xs:
        y = xs[0]
        if y >= 5:
            xs.pop(0)
        else:
            break


def h(xs):
    while xs:
        y = xs.pop()
        if y > 3:
            break
    else:
        return None
    return y


def k(xs):
    for y in xs:
        if y > 3:
            break
    else:
        return None
    return xs
def b4b03_shallow(xs, k):
    try:
        v = xs[0]
    except IndexError:
        v = -1
    else:
        v = v + k
    return v


def b4b03_deep(xs, k, flag):
    if flag:
        if k > 0:
            try:
                v = xs[0]
            except IndexError:
                v = -1
            else:
                v = v + k
    return v

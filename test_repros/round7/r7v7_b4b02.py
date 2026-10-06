def b4b02_shallow(xs, k):
    try:
        i = xs.index(k)
    except ValueError:
        return -1
    return i


def b4b02_deep(xs, k, flag):
    if flag:
        try:
            if k > 0:
                i = xs.index(k)
            else:
                i = -2
        except ValueError:
            return -1
        return i
    return -3

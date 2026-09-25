def inner_only(x):
    try:
        v = int(x)
    except ValueError:
        v = -1
    else:
        v = v * 2
    return v


def wrapped(x):
    try:
        try:
            v = int(x)
        except ValueError:
            v = -1
        else:
            v = v * 2
        w = v + 1
    except TypeError:
        w = 0
    return w

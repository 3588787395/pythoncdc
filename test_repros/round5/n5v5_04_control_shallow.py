def n_elif(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    return 'c'


def n_for_else(xs):
    for x in xs:
        r = x
    else:
        r = 0
    return r


def n_aug(x):
    y = x
    y += 1
    return y


def n_global():
    global _NG
    _NG = 1
    return _NG


def n_ann(x):
    a: int = x
    return a

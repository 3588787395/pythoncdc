_GNC = 0


def gn_root():
    global _GNC
    _GNC += 1
    return _GNC


class CGnc:
    def m(self):
        global _GNC
        _GNC -= 1
        return _GNC


def gn_deep():
    def mid():
        def inner():
            global _GNC
            _GNC = 9
        for i in range(2):
            if i:
                inner()
    mid()
    return _GNC


def gn_nonlocal_chain():
    c = 0

    def l1():
        def l2():
            def l3():
                nonlocal c
                c += 1
            l3()
        l2()
    l1()
    return c


def gn_both():
    global _GNC
    c = 0

    def inc():
        nonlocal c
        c += 1
    _GNC += c
    return _GNC


def gn_loop():
    global _GNC
    r = 0
    while _GNC < 5:
        _GNC += 1
        r = _GNC
    return r


def gn_match(x):
    global _GNC
    match x:
        case 0:
            _GNC += 1
        case _:
            _GNC -= 1
    return _GNC

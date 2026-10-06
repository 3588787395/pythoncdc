_G = 0


def e01_global():
    global _G
    _G += 1
    return _G


def e02_shallow():
    global _G
    _G = 1
    return _G


def e03_deep():
    def inner():
        global _G
        _G += 2
        return _G
    r = 0
    for i in range(2):
        if i:
            r = inner()
    return r


def make():
    c = 0

    def inc():
        nonlocal c
        c += 1
        return c
    return inc


class CG:
    def m(self):
        global _G
        _G -= 1
        return _G


def e04_nonlocal_deep():
    c = 0

    def outer():
        def inner2():
            nonlocal c
            c += 10
        for i in range(2):
            if i:
                inner2()
    outer()
    return c


def e05_global_in_loop():
    global _G
    r = 0
    while _G < 5:
        _G += 1
        r = _G
    return r


def e06_both():
    global _G
    c = 0

    def inc():
        nonlocal c
        c += 1
    _G += c
    return _G


def e07_nested_global():
    def mid():
        def inner():
            global _G
            _G = 9
        inner()
    mid()
    return _G


def e08_nonlocal_comp():
    c = 0

    def bump(xs):
        nonlocal c
        for x in xs:
            c += x
    bump([1, 2])
    return c


def e09_global_cond():
    global _G
    if _G > 0:
        _G += 1
    else:
        _G -= 1
    return _G

MOD_AN: int = 0
MOD_AN2: 'list'
MOD_AN3: dict = {}


def ann_root(x):
    a: int = x + 1
    b: str
    c: dict = {}
    d: list = []
    return a, b, c, d


def ann_deep(x, xs):
    r = 0
    for i in xs:
        if i:
            a: int = i
            while a > 0:
                a -= 1
            r = a
    return r


class CAnn:
    cv: int = 5
    cv2: str

    def m(self, x, xs):
        a: int = x
        for i in xs:
            if i:
                b: int = i
        with open('a') as f:
            c: int = x
        try:
            d: int = x
        finally:
            pass
        match x:
            case 0:
                e: int = 1
            case _:
                e = 0
        return a, b, c, d, e


def ann_closure(x):
    c: int = 0

    def inc():
        nonlocal c
        c += 1
        return c
    return inc


def ann_nested3(x):
    def l1():
        def l2():
            def l3():
                z: int = x
                return z
            return l3()
        return l2()
    return l1()

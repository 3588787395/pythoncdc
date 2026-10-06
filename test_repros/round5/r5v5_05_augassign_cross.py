MOD_AA = 1
MOD_AA += 2
MOD_AA *= 3


def aug_root(x):
    y = x
    y += 1
    y //= 2
    y **= 2
    y &= 7
    return y


class CAug:
    CV = 1
    CV += 2

    def m(self, xs):
        for i in xs:
            if i:
                self.v += i
            elif i < 0:
                self.v -= i
            else:
                self.v = 0
        with open('a') as f:
            self.w += 1
        try:
            self.z += 1
        finally:
            self.z -= 1
        match xs:
            case []:
                self.q += 1
            case _:
                self.q -= 1
        return self.v


def aug_deep(x, xs):
    r = 0
    for i in xs:
        while i > 0:
            if i:
                r += i
                i -= 1
    return r


def aug_nonlocal(x):
    c = 0

    def inc():
        nonlocal c
        c += 1

    def outer():
        def inner():
            nonlocal c
            c += x
        inner()
    outer()
    return c


_GAA = 0


def aug_global():
    global _GAA
    _GAA += 1
    return _GAA

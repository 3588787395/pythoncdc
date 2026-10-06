def e01_root(x):
    y = x
    y += 1
    y -= 2
    y *= 3
    y //= 2
    y %= 5
    y **= 2
    return y


def e02_bit(x):
    y = x
    y &= 7
    y |= 8
    y ^= 3
    y <<= 1
    y >>= 2
    return y


def e03_deep(x, xs):
    for i in range(3):
        if i:
            xs[0] += i
            xs[1] -= i
    return xs


def e04_boolop_rhs(x, a, b):
    r = x
    r += (a or b)
    return r


def e05_attr(obj):
    obj.v += 1
    obj.v *= 2
    return obj.v


def e06_matmul(M, N):
    M @= N
    return M


def e07_b76_deep(x, a, b):
    r = x
    for i in range(2):
        if i:
            r += (a and b) or a
    return r


class CAU:
    def m(self, x):
        self.v = x
        self.v += 1
        self.v //= 2
        return self.v


def e08_shallow(x):
    y = x
    y += 1
    return y


def e09_close(x):
    c = 0

    def inc():
        nonlocal c
        c += 1
        return c
    return inc

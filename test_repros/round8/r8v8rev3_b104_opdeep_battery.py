def v1(x, f, sink):
    # B104-R2a 域内深探：链 + and 尾操作数 = 海象（值段含 COPY(1)+STORE 的操作数重建）
    n = 0
    while 0 < x < 10 and (y := f(x)):
        x += y
        n += 1
    return n, y


def v2(x, flag, limit):
    # B104-R2a 域内深探：链 + 多操作数 and 尾（chain and a and b 同判声称）
    n = 0
    while 0 < x < 10 and flag and x < limit:
        x += 1
        n += 1
    return n


def v3(flag, g2, a, b, c):
    # B104-R2a 域内深探：多操作数前置 and 首（a and b and 链 镜像序声称）
    while flag and g2 and 0 < a < b < c:
        a += 1
    return a

def w2_plain(x, n):
    # B104-R4 边界：while 宿主 2 元链（预期绿：v3 tip 亦绿）
    r = 0
    while 0 < x < n:
        x += 1
        r += 1
    return r


def w3_plain(x, n):
    # B104-R4：while 宿主 3 元链 + 体含 store（e08_while 同形族）
    r = 0
    while 0 < x < n < 100:
        x += 1
        r += 1
    return r


def w3_nostore(x, n, out):
    # B104-R4：while 宿主 3 元链 + 体无 store（append 位形）
    while 0 < x < n < 100:
        out.append(x)
        x += 1
    return out


def w4_call(x, n, s):
    # B104-R4：while 宿主 4 元链 + Call 末操作数
    while 0 < x < n < len(s) < 100:
        x += 1
    return x


def w3_deep(x, n, ys):
    # B104-R4：深度 ≥2 宿主——for 体内的 while 宿主 3 元链（C2 无感判据）
    for y in ys:
        while 0 < y < n < 100:
            y += 1
    return n


def w3_and(x, n, flag):
    # B104-R4：while 宿主链 + and 混合（chain4 v2 同形族）
    r = 0
    while 0 < x < n and flag:
        x += 1
        r += 1
    return r


def neg_for3(x, ys):
    # 负对照：for 宿主 3 元链（预期绿：nb_for/v1/v5 域）
    out = []
    for y in ys:
        if 0 < y < x < 100:
            out.append(y)
    return out


def neg_ret3(a, b, c):
    # 负对照：return 位 3 元链（预期绿：v3/e01 域）
    return a < b < c

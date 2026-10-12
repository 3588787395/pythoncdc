def v1(y):
    # B104: 4 元链 for 宿主（dispatch 变体 1）
    out = []
    for x in y:
        if 0 < x < 10 < x * 2 < 100:
            out.append(x)
    return out


def v2(x, flag):
    # B104: while 头链式比较 + and 混合条件（守卫 H5 声称不误伤的混合形）
    n = 0
    while 0 < x < 10 and flag:
        x += 1
        n += 1
    return n


def v3(a, b, c):
    # B104: 链含 Call 末操作数（return 位值链）
    return a < b < len(c)


def v4(x):
    # B104: 4 元链 while 宿主 + 体语句（回边重检 + 前驱语句）
    n = 0
    while 0 < x < 10 < x * 2 < 100:
        x += 1
        n += 1
    return n


def v5(y, k):
    # B104: 4 元链 for 宿主 + continue 混合体（宿主交叠外推）
    out = []
    for x in y:
        if 0 < x < k < x * 2 < 100:
            continue
        out.append(x)
    return out

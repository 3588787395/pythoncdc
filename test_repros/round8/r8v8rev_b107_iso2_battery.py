def u1(o, p, k, v, w):
    # 4 目标链 + 前置语句
    s = v + w
    o.a = p[k] = o.b = p[w] = s
    return s


def u2(o, p, k, v):
    # 3 目标链 + 前置语句（无 return 消费）
    s = v * 2
    o.a = p[k] = o.b = s
    return o.a


def u3(o, p, k, v):
    # 2 目标链 + 前置语句（判据族原通过形态对照）
    s = v * 3
    o.a = p[k] = s
    return o.a

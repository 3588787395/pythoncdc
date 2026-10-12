class Q2:
    r = 0


def t1(o, p, k, v, q):
    # 3 目标混合链（q 为形参，无前置构造）
    o.a = p[k] = q.r = v
    return o.a, p[k], q.r


def t2(o, p, k, v):
    # 3 目标混合链 + 前置局部构造（class call）
    q = Q2()
    o.a = p[k] = q.r = v
    return o.a, p[k], q.r


def t3(o, p, k, v, w):
    # 3 目标混合链（纯局部名值 + 前置算术语句）
    s = v + w
    o.a = p[k] = o.b = s
    return s

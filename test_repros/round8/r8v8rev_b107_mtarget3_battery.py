class Q:
    def __init__(self):
        self.r = 0


def v1(o, p, k, v):
    # B107: 3 目标复杂链 o.a = p[k] = q.r = v（STORE_ATTR/STORE_SUBSCR 混合链）
    q = Q()
    o.a = p[k] = q.r = v
    return o.a, p[k], q.r


def v2(c, d, e, f):
    # B107: UNPACK_EX 星号解包链 a, *b = c, *d = e, f（双组星号解包目标）
    a, *b = c, *d = e, f
    return a, b


def v3(o, p, k, v, w):
    # B107: 4 目标复杂链（两属性两下标交错）+ 链后语句
    o.a = p[k] = o.b = p[w] = v
    return len(p)

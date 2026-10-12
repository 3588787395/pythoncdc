def v1(f, a, b, kw):
    # B106: 星 + 双星混合实参
    return f(a, *b, **kw)


def v2(f, a, b):
    # B106: 双星位置实参（非尾双星）
    return f(*a, *b)


def v3(k, a):
    # B106: lambda *a + **k 形参 + 内层星调用
    g = lambda *a, **k: k(*a)
    return g(*a, m=1)


def v4(f, xs, d):
    # B106: 星实参作推导式元素 + 外层星键（组合位）
    return [f(*xs, v) for v in d]

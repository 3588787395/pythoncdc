"""逐字复刻 r19c_04_anchor_try_finally（既有锚点形状：if 内含 try/finally）"""


def f(items, g):
    for x in items:
        if x:
            try:
                g(x)
            finally:
                g(0)

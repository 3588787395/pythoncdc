"""逐字复刻 r19c_23_neg_continue_in_try_finally（既有负对照形状）"""


def f(items, g):
    for x in items:
        try:
            if x:
                continue
            g(x)
        finally:
            g(0)

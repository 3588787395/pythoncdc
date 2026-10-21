"""AT-02: while x try x for —— 三元嵌套，for-else + try-else 混合"""


def a4(xs):
    while True:
        try:
            for x in xs:
                if x:
                    break
                else:
                    continue
        except Exception:
            break
        else:
            continue

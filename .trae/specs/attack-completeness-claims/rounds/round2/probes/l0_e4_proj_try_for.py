"""AT-02 二元投影 4/5（修正）: try x for（a4 的 try+for 子投影）"""


def e4(xs):
    try:
        for x in xs:
            print(x)
    except Exception:
        pass

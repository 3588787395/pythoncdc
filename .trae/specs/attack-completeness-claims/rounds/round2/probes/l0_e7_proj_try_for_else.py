"""AT-04 二元投影: try x for-else（b5 的 try+for-else 子投影）"""


def e7(xs):
    try:
        for x in xs:
            print(x)
        else:
            print('else')
    except Exception:
        pass

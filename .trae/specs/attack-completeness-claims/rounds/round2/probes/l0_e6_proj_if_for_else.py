"""AT-04 二元投影: if x for-else（b5 的 if+for-else 子投影）"""


def e6(xs):
    if xs:
        for x in xs:
            print(x)
        else:
            print('else')

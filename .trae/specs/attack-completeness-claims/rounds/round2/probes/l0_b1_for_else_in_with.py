"""AT-04: for-else 位于 with 体内（守卫只列 TryExceptRegion 的子集检验）"""


def b1(xs):
    with open('f') as fh:
        for x in xs:
            print(x)
        else:
            print('for-else')
    return fh

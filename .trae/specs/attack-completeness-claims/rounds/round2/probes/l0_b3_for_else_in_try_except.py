"""AT-04: for-else 位于 try/except 体内（无 finally）"""


def b3(xs):
    try:
        for x in xs:
            print(x)
        else:
            print('else')
    except Exception:
        pass

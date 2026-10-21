"""AT-04: for-else 位于 try 体内的 if 分支中"""


def b5(xs):
    try:
        if xs:
            for x in xs:
                print(x)
            else:
                print('else')
    except Exception:
        pass

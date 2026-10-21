"""AT-04 语义强化: for-else 体含 break 时，else 归属错误即产生**可观测语义差**"""


def e8(xs):
    try:
        if xs:
            for x in xs:
                if x:
                    break
                print(x)
            else:
                print('else')
    except Exception:
        pass

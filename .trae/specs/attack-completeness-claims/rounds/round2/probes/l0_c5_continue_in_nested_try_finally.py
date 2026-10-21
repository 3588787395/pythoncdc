"""AT-01/AT-04: try/finally 内 continue，finally 副本与 continue 目标双重归属"""


def c5(xs):
    for a in xs:
        try:
            if a:
                continue
        finally:
            print('fin')

"""AT-01/AT-04: finally 副本 + continue —— 副本归属与 continue 目标同时命中"""


def c4(xs):
    for a in xs:
        try:
            continue
        finally:
            print('fin')

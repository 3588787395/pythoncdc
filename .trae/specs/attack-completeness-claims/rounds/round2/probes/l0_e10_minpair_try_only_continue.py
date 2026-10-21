"""AT-02/AT-04 最小对 B: try 体只有 continue（无 if）"""


def e10(xs):
    for a in xs:
        try:
            continue
        finally:
            print('fin')

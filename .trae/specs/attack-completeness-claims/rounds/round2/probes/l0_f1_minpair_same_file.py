"""AT-02/AT-04 同文件最小对：m1 与 m2 唯一差异 = try 体末尾多一条 g(x)"""


def m1(items, g):
    for x in items:
        try:
            if x:
                continue
        finally:
            g(0)


def m2(items, g):
    for x in items:
        try:
            if x:
                continue
            g(x)
        finally:
            g(0)

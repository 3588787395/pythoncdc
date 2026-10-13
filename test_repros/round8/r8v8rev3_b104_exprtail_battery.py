def v1(x, r):
    # B104-R2a None-skip 路径压力：and 尾操作数 = f-string（FORMAT_VALUE/BUILD_STRING 求值段）
    n = 0
    while 0 < x < 10 and f'{x}':
        x += 1
        n += 1
    return n


def v2(x, q, r):
    # B104-R2a None-skip 路径压力：and 尾操作数 = 字典推导式（内层 code object）
    n = 0
    while 0 < x < 10 and {k: x for k in r}:
        x += 1
        n += 1
    return n


def v3(x, y):
    # B104-R2a None-skip 路径压力：and 尾操作数 = 条件表达式（IfExp 短路位形）
    n = 0
    while 0 < x < 10 and (y if y else x):
        x += 1
        n += 1
    return n

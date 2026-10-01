# n2_03 负对照：普通 while（非混合条件）+ try（强制 MATCH）
# 焦点：while×try 无混合链时零交互回退


def f(n, d):
    acc = 0
    while n > 0:
        try:
            acc += d[n]
        except KeyError:
            acc -= 1
        n -= 1
    return acc

# rv_09 修复二 ternary BoolOp 驱动链升级 嵌套变体：
# 混合链三元 `1 if a and b or c else 2` 位于 while 体内（while > ifexp）
# 验收：深层与浅层 r1_11 产物一致


def f(a, b, c):
    acc = []
    n = 0
    while n < 4:
        acc.append(1 if a and b or c else 2)
        n += 1
    return acc

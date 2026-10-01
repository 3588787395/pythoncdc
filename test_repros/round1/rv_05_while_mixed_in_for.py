# rv_05 修复二 while 双向续接 嵌套变体 1：
# `while a and b or c:` 位于 for 体内（for > while），带 if-break
# 同时覆盖 region_ast_generator 的 if-break 过滤三分


def f(n, a, b, c):
    s = 0
    for _ in range(n):
        while a and b or c:
            s += 1
            if s > 9:
                break
        s += 2
    return s

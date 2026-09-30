# -*- coding: utf-8 -*-
# 负对照：`if x is not None:` + 纯顺序体（无 if/for/assert 子结构、
# 守卫块前无多语句）。当前代码应正确处理 → MATCH。
def f(x, y):
    total = 0
    if x is not None:
        total += len(x)
        total += y
    return total

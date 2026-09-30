# -*- coding: utf-8 -*-
# 负对照：简单 `if A and B: X else: Y`（无前导语句块、elif、守卫嵌套）。
# 当前代码应正确处理 → MATCH。
def f(a, b):
    if a and b:
        return 1
    else:
        return 2

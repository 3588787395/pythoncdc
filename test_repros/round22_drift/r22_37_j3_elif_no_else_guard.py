# -*- coding: utf-8 -*-
# R22 负对照 37 —— 与锚点 28 只差一个 `else: pass`（没有边界 NOP 可折叠）。
#
# J3' 无操作对象；同时它是 28 的"缺失半"对照：证明 28 的 −1 确实来自
# else 臂那个 NOP，而不是 elif 链本身。本复现：base=MATCH after=MATCH。类别 GUARD。
def f(mode, b):
    if mode == 1:
        if b:
            print(1)
    elif mode == 2:
        if b:
            print(2)
    print('tail')

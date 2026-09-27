# -*- coding: utf-8 -*-
# synth a02 -- 负例对照：真·嵌套 if-else（内外两层失败出口不同块）。
# 期望：landed 与 abs1 输出逐字节相同（same-target 豁免不得命中，仍走 IfRegion 层级）。
def synth_a02_true_nested(a, b, x):
    if a:
        if b:
            x = 1
        else:
            x = 2
    else:
        x = 3
    if a:
        if b:
            x = x + 1
    return x

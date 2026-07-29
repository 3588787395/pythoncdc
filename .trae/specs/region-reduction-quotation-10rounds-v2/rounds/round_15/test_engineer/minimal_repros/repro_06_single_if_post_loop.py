"""复现 06：单 if（无 elif）+ 后置循环块。

模式：最简形态 — 单 if 分支 + 后置循环。
JUMP_FORWARD 跳过/进入后置循环的最小复现。
"""
def f(cond, xs, ys):
    out = []
    if cond:
        for x in xs:
            out.append(x)
    for y in ys:
        out.append(y)
    return out

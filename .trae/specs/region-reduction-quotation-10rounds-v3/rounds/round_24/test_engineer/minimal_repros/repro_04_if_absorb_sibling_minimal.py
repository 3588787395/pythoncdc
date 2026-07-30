"""repro_04 — 缺陷1最小化: for 循环 + if/elif(break)/else + 单个兄弟 if。

最简形式：then 与 else 均跳到循环末尾的兄弟 if，elif 为 break。兄弟 if 被并入 then。
（单纯 if/else + 单兄弟 if 不触发，需 break 分支制造 JUMP_FORWARD 到循环出口。）
"""
def f(items):
    pre = None
    out = []
    for n in items:
        if pre is None:
            out.append(n)
        elif n == 0:
            break
        else:
            out.append(n + 1)
        if pre != n:
            pre = n
    return out

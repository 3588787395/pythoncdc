"""复现 02：if/elif/else 链 + 后置单层循环块。

模式：单层 for 循环作为后置块，JUMP_FORWARD 跳过/进入循环。
区域 [lo, hi) 含 FOR_ITER(exit=hi) + JUMP_BACKWARD(->FOR_ITER)。
"""
def f(flag, days, times):
    out = []
    if flag == 1:
        for d in days:
            out.append(d)
    elif flag == 2:
        for d in days:
            out.append(d.upper())
    else:
        out.append('none')
    for t in times:
        out.append(t)
    return out

"""复现 05：分支含 listcomp + 后置循环块。

模式：if 分支内含 listcomp（独立 code 对象，与 build_future_fill_time @idx201 一致），
分支末尾 JUMP_FORWARD 跳过/进入后置循环。listcomp code 对象本身在 orig/new 一致，
差异仅在外层 JUMP_FORWARD 目标偏移。
"""
def f(typet, days, items):
    total = []
    if typet == 1:
        formatted = [str(i) for i in items]
        for d in days:
            for t in formatted:
                total.append(d + t)
    elif typet == 2:
        for d in days:
            for t in items:
                total.append(d + str(t))
    for d in days:
        for t in items:
            total.append(d + ' ' + str(t))
    return total

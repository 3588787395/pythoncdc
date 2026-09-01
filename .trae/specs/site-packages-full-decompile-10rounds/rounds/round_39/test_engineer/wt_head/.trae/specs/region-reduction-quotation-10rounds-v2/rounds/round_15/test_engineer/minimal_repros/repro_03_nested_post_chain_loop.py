"""复现 03：多分支 if/elif 链 + 后置嵌套循环块。

模式：后置块为嵌套循环（外层 FOR_ITER exit=hi，内层 FOR_ITER exit=外层 JUMP_BACKWARD）。
对应 build_future_fill_time 的实际结构（两层 for 循环作为后置块）。
"""
def f(kind, all_days, am_times, pm_times):
    result = []
    if kind == 1:
        for d in all_days:
            for t in am_times:
                result.append(d + t)
    elif kind == 2:
        for d in all_days:
            for t in pm_times:
                result.append(d + t)
    for d in all_days:
        for t in pm_times:
            result.append(d + ' ' + t)
    return result

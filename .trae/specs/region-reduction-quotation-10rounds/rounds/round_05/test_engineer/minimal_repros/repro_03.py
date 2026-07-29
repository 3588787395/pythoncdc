"""repro_03: 复现 build_future_fill_time 反编译缺陷（for loop 应在 else 内部但被拉到函数体）。

缺陷模式：
    if cond: ...
    else:
        if nested_cond: ...
        elif ...: ...
        else: ...
        for item in market_time: ...   # 应在 else 分支内，但被拉到函数体顶层

根因：else 分支内嵌套 if-elif-else 归约后，紧随其后的 for 循环未被纳入 else 分支体，
被错误地提升到函数体层级。违反原则 3（嵌套即抽象节点）—— for 应作为 else 分支的尾随语句。
"""


def build_future_fill_time(cond, typet, market_time):
    if cond:
        total_dts = []
    else:
        if typet == 2:
            total_dts = [1, 2]
        elif typet == 3:
            total_dts = [3, 4]
        else:
            total_dts = [5, 6]
        for item in market_time:
            total_dts.append(item)
    return total_dts

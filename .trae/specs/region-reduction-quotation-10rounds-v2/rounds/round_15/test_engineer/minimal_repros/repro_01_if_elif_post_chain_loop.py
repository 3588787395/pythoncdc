"""复现 01：if/elif 分支后置循环 — JUMP_FORWARD 跳过/进入循环块差异。

模式：if/elif 链的分支各自有"自有循环"，链末尾有"后置循环"。
orig 中分支末尾 JUMP_FORWARD 跳到后置循环之后（跳过循环块），
new（反编译）中 JUMP_FORWARD 跳到后置循环开头（进入循环块）。

对应函数：build_future_fill_time @idx226 (JUMP_FORWARD ->[649] vs ->[629])
区域 [629, 649) 为自包含循环块（FOR_ITER exit=649, JUMP_BACKWARD->FOR_ITER）。
"""
def f(typet, trade_days, trade_times, market_time):
    total = []
    if typet == 1:
        for today in trade_days:
            for item in trade_times:
                total.append(today + item)
    elif typet == 2:
        for today in trade_days:
            for item in trade_times:
                total.append(today + item)
    for today in trade_days:
        for item in market_time:
            total.append(today + ' ' + item)
    return total

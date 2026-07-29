"""R8 repro_07: build_future_fill_time listcomp code 对象差异。
缺陷: 函数内 3 个 listcomp 中某个的内部 code 对象与原始不一致，引发后续跳转目标偏移(instr_diff)。
区域类型: Loop + listcomp  违反原则: 3(嵌套即抽象节点)
"""
def f(start, end, holidays):
    all_days = range(start, end)
    trade_days = [d for d in all_days if d not in holidays]
    am = [d for d in trade_days if d < 12]
    pm = [d for d in trade_days if d >= 13]
    result = []
    for d in trade_days:
        if d in am:
            result.append(('am', d))
        elif d in pm:
            result.append(('pm', d))
    return result

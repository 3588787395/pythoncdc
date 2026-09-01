# R5 minimal repro: 比较表达式 + binop 括号丢失 -> 运算符优先级错误
# 关联缺陷：quotation.pyc get_str_data line 519  filled.index >= nowstart & filled.index <= nowend
#           / change_his_to_backward line 858  datetime.now() + qdt.timedelta(-1).strftime(...)
#           (新发现, R4 未覆盖)
# 触发区域：COMPARE / _identify_chained_compare_regions + _identify_boolop_regions
#           (含 & 的 (a >= b) & (c <= d) 表达式括号丢失, 优先级退化为 a >= (b & c) <= d)
# 预期：mask = (idx >= nowstart) & (idx <= nowend)
# R5 实际产物：mask = idx >= nowstart & idx <= nowend   (& 括号丢失, 优先级错误)


def filter_range(df, nowstart, nowend):
    idx = df.index
    mask = (idx >= nowstart) & (idx <= nowend)
    return df[mask]

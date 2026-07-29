"""repro_10: 三元表达式嵌套在方法调用参数中（fill_minute_or_day_blank 变体）。

复现原始字节码结构：source_start[:8] + (len(source_start[8:]) == 4 and source_start[8:] or '0000')
即三元/and/or 混合表达式作为 strptime 的参数。反编译器可能错误归约 BoolOp/Ternary。
对应 _identify_ternary_regions / _identify_boolop_regions / _generate_ternary。
"""


def parse_source(source_start, source_end):
    source_start = qdt.datetime.strptime(source_start[:8] + (len(source_start[8:]) == 4 and source_start[8:] or '0000'), '%Y%m%d%H%M')
    source_end = qdt.datetime.strptime(source_end[:8] + (len(source_end[8:]) == 4 and source_end[8:] or '1530'), '%Y%m%d%H%M')
    if source_start < source_end:
        result = source_start + (source_end - source_start)
    else:
        result = source_end
    return result

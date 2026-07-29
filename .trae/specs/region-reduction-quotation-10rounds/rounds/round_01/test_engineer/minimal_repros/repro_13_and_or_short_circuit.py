"""repro_13: and/or 混合短路 + 字符串切片拼接（fill_minute_or_day_blank 变体）。

复现原始字节码结构：source_end[8:] or '1530' 即 or 短路表达式赋值，
配合前置的 and 短路 ternary。反编译器可能错误归约 BoolOp。
对应 _identify_boolop_regions / _generate_boolop。
"""


def parse_endpoints(source_start, source_end):
    source_start = source_start[:8] + (len(source_start[8:]) == 4 and source_start[8:] or '0000')
    source_end = source_end[:8] + (source_end[8:] or '1530')
    if source_start < source_end:
        result = source_start + source_end
    else:
        result = source_end + source_start
    return result

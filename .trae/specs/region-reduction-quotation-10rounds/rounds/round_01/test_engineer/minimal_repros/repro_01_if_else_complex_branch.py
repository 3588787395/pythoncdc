"""repro_01: 三元表达式赋值 + and 短路（fill_minute_or_day_blank 模式）。

复现原始字节码结构：
  code = stocks.split('.')[0]
  suffix = stocks.split('.')[1]
  suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
反编译器把 ternary 与前置方法调用合并，产生错误源码（少 54 条）。
对应 _identify_ternary_regions / _generate_ternary + _identify_boolop_regions。
"""


def fill_blank(stocks):
    code = stocks.split('.')[0]
    suffix = stocks.split('.')[1]
    suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
    source_start = suffix
    source_end = suffix
    dts = get_fill_time(suffix, source_start, source_end)
    if len(dts) > 0:
        result = parse_time(source_start, source_end)
        if result is not None:
            back = build_back(dts)
            klines = concat([result, back])
        else:
            pre = build_pre(dts)
            klines = concat([pre, result])
    return klines

"""repro_20: 三元表达式作为 return 值 + and/or 短路（fill_minute_or_day_blank 变体）。

原始 fill_minute_or_day_blank 含三元与 and 短路混合，反编译器把三元条件含 and 的
右操作数误并入前序语句。本 repro 聚焦 Ternary 作为 return 表达式 + and/or 短路归约缺陷。
"""


def fill_blank(stocks, suffix, code):
    code = stocks.split('.')[0]
    suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
    return suffix if suffix.startswith('T.') else suffix

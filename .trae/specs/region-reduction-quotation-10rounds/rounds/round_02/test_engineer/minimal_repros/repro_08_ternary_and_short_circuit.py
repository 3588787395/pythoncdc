"""repro_08: 三元表达式含 and 短路 + 字符串切片拼接（fill_minute_or_day_blank ternary）。

原始 fill_minute_or_day_blank 的三元：
    suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
条件含 and 短路 + code[:1] 切片，反编译器把 and 右操作数误并入三元，丢失前序 code 赋值。
本 repro 聚焦 Ternary 条件含 BoolOp(and) 短路 + 切片的归约缺陷。
"""


def parse_suffix(stocks, suffix):
    code = stocks.split('.')[0]
    suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
    return suffix

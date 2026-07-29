"""repro_06: 复现 fill_minute_or_day_blank 反编译缺陷（杂散字符串字面量）。

缺陷模式：`source_end = source_end[8:] or '1530'` 反编译后产生杂散的
三引号 '1530' 字符串字面量（or 表达式重建错误）。

根因：`X or 'literal'` 短路表达式中，当 X 为 BINARY_SUBSCR 切片结果时，
BoolOp 归约将常量分支误发射为独立字符串表达式语句，而非合并到赋值右侧。
"""


def fill_blank(source_end):
    source_end = source_end[8:] or '1530'
    return source_end

"""repro_06: 顺序 if 重赋值 + 长 or 链条件（load_get_price 模式）。

复现原始字节码结构：连续 if 语句对 typet 比较并重赋值 _typet/typet，
后接 if len(panel.major_axis) != 0: 内嵌 if is_utc == '0' and typet == 1 or typet == 2 or ...
反编译器丢失尾部 isinstance/str 分支（少 19 条）。
对应 _identify_conditional_regions + _identify_boolop_regions 长 or 链。
"""


def load_get_price(typet, stocks, start, end):
    _typet = 6
    if typet == 7:
        _typet = 7
        typet = 6
    if typet == 8:
        _typet = 8
        typet = 6
    if typet == 9:
        _typet = 9
        typet = 6
    if typet == 15:
        _typet = 15
        typet = 6
    panel = load_bars(stocks, typet, start, end)
    if len(panel.major_axis) != 0:
        if is_utc == '0' and typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13:
            panel = panel.tz_localize('UTC')
        else:
            panel = panel.tz_localize('UTC')
    if isinstance(stocks, str):
        rdata = panel[stocks]
    else:
        rdata = panel
    return rdata

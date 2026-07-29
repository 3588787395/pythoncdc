"""repro_04: 长 or 链作为 if-and 内层条件，分支体被折叠（load_get_price 模式）。

原始 load_get_price 中：
    if len(panel.major_axis) != 0:
        if is_utc == '0':
            if typet == 1 or typet == 2 or typet == 3 or typet == 4:
                panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
            elif _typet in (7, 8, 9, 15):
                panel = get_str_data(panel, count, _typet)
反编译器把 or 链 if 条件+分支体折叠，直接跳到 tz_convert 体，丢失 or 链测试与 elif 分支。
本 repro 聚焦 BoolOp 长 or 链 + 嵌套 if + elif(in) 分支体归约。
"""


def load_get_price(stocks, typet, start, end, count, is_utc):
    panel = get_data(stocks, typet, start, end)
    if len(panel.major_axis) != 0:
        if is_utc == '0':
            if typet == 1 or typet == 2 or typet == 3 or typet == 4:
                panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
            elif typet in (7, 8, 9, 15):
                panel = get_str_data(panel, count, typet)
        else:
            panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    if isinstance(stocks, str):
        rdata = panel[stocks]
    else:
        rdata = panel
    return rdata

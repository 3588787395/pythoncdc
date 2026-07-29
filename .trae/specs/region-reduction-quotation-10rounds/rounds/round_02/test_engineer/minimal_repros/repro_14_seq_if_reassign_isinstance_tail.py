"""repro_14: 顺序 if 重赋值 + 尾部 isinstance 分支丢失（load_get_price 模式）。

原始 load_get_price 连续 4 个 `if typet == N: _typet = N; typet = 6` 重赋值后，
`if len(panel.major_axis) != 0:` 内嵌长 or 链，尾部 `isinstance(stocks, str)` 分支
（panel = panel[stocks] / panel = panel）丢失（-25 指令）。本 repro 聚焦
Conditional 顺序 if 重赋值 + 尾部 isinstance 三元归约缺陷。
"""


def load_get_price(stocks, typet, start, end, count, fq=None):
    if typet == 1:
        _typet = 1
        typet = 6
    if typet == 2:
        _typet = 2
        typet = 6
    if typet == 3:
        _typet = 3
        typet = 6
    if typet == 4:
        _typet = 4
        typet = 6
    if _typet in (7, 8, 9, 15):
        panel = get_str_data(panel, count, _typet)
    if isinstance(stocks, str):
        rdata = panel[stocks]
    else:
        rdata = panel
    return rdata

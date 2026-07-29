"""repro_05: 长 or 链 `is_utc=='0' and (typet==1 or ... or typet==13)` + 前导嵌套 if（load_get_price）。

R3 修复在精简 repro 上有效，但 load_get_price 的原始 CFG 含 `if len(panel.major_axis) != 0:` 前导嵌套 if，
未触发与精简 repro 相同的代码路径。本 repro 镜像原始 CFG：前导 if + 长 or 链 + elif。

镜像 load_get_price 的实际 CFG：
  - if len(panel.major_axis) != 0:（前导嵌套 if）
    - if is_utc == '0' and (typet == 1 or typet == 2 or ... or typet == 13):
        panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
    - elif typet == 6:
        panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
  - if _typet in (7, 8, 9, 15): panel = get_str_data(panel, count, _typet)
"""


def load_get_price_repro(panel, is_utc, typet, count, _typet, stocks):
    if len(panel.major_axis) != 0:
        if is_utc == '0' and (typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13):
            panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
        elif typet == 6:
            panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    if _typet in (7, 8, 9, 15):
        panel = get_str_data(panel, count, _typet)
    if isinstance(stocks, str):
        rdata = panel[stocks]
    else:
        rdata = panel
    return rdata

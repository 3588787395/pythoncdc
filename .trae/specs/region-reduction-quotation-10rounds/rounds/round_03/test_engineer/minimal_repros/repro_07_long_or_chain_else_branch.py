"""repro_07: 长 or 链 + else 分支体丢失（load_bars_from_hundsun / load_get_price 变体）。

聚焦 `if is_utc=='0' and (typet==1 or typet==2 or typet==3 or typet==4):` 长 or 链
+ else 分支（而非 elif）。反编译器把 or 链 if 分支体折叠为 pass，仅保留 else 分支。
本 repro 聚焦 BoolOp 长 or 链 + else 分支体归约。
"""


def adjust_panel_else(panel, is_utc, typet):
    if is_utc == '0' and (typet == 1 or typet == 2 or typet == 3 or typet == 4):
        panel.major_axis = panel.major_axis.tz_localize('Asia/Shanghai').tz_convert('UTC')
    else:
        panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    return panel

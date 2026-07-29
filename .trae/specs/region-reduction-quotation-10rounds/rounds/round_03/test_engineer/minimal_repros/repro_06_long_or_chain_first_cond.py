"""repro_06: 长 or 链作为 if 首条件 + elif 兜底，分支体丢失（load_bars_from_hundsun 变体）。

聚焦 `if (typet==1 or typet==2 or ... or typet==13) and is_utc=='0':` 长 or 链作为
首条件 + elif 兜底。反编译器把 or 链 if 分支体折叠为 pass，丢失主分支逻辑。
"""


def adjust_panel_first(panel, is_utc, typet):
    if (typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13) and is_utc == '0':
        panel.major_axis = panel.major_axis.tz_localize('Asia/Shanghai').tz_convert('UTC')
    elif typet == 6:
        panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    return panel

"""repro_10: 长 or 链 + elif 分支 tz_localize 体丢失（load_bars_from_hundsun 变体）。

聚焦 `if a and (x==1 or x==2 or ... or x==13):` 长 or 链 + elif 兜底分支。
反编译器把 or 链 if 分支体折叠为 pass，仅保留 elif 分支，丢失主分支 tz 转换逻辑。
"""


def adjust_panel(panel, is_utc, typet):
    if len(panel) > 0:
        if is_utc == '0' and (typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13):
            panel.major_axis = panel.major_axis.tz_localize('Asia/Shanghai').tz_convert('UTC')
        elif typet == 6:
            panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    return panel

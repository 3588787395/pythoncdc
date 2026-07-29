"""repro_09: 长 if/elif 链 + 方法调用链截断（load_bars_from_hundsun 模式）。

复现原始字节码结构：if typet == 6: ... 后接 if is_utc == '0' and (typet==1 or typet==2 or ...)
每个分支含 tz_localize('Asia/Shanghai').tz_convert('UTC') 方法调用链，
反编译器把长 or 链折叠为单 if + pass，丢失 tz_localize/tz_convert 分支（少 150 条）。
对应 _identify_boolop_regions 长 or 链 + _identify_conditional_regions 嵌套。
"""


def convert(typet, panel, is_utc):
    if typet == 6:
        panel = panel.tz_localize(pytz.utc)
    if is_utc == '0':
        if typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13:
            panel.major_axis = panel.major_axis.tz_localize('Asia/Shanghai').tz_convert('UTC')
        else:
            panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    else:
        if typet == 6:
            panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    if not panel.empty:
        panel = pandas.concat([panel, panel], axis=0)
    return panel

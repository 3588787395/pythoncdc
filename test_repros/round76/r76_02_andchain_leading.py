# -*- coding: utf-8 -*-
# R76-A1 复现（对照 Quote.load_get_price）：外层单操作数守卫 if len(...)!=0，
# 内层 `if is_utc == '0' and typet in T:` + elif。预期缺陷：外层守卫物化为
# 裸表达式，内层 and 链拆成嵌套 if，elif 挂接层级改变。
def f(panel, is_utc, typet):
    panel = load(panel)
    if len(panel.major_axis) != 0:
        if is_utc == '0' and typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
        elif typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_localize('UTC').tz_convert('Asia/Shanghai')
    return panel

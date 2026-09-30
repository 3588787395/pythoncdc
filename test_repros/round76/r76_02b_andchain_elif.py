# -*- coding: utf-8 -*-
# R76-A1 变体（探边界）：平铺 if A and B: X elif D: Y（无外层守卫）。
def f(panel, is_utc, typet):
    if len(panel) != 0 and is_utc == '0':
        panel.convert('Asia/Shanghai')
    elif typet in (1, 2, 3):
        panel.localize('UTC')
    return panel

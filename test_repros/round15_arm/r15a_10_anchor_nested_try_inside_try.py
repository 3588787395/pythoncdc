# -*- coding: utf-8 -*-
"""R15-A 10 anchor nested try inside try
10 子 if 本身已在 try 里（层级多一层，检验「孙辈被挂到祖父臂」是否成串发生）。

真实目标：site-packages/IQEngine/utils/logger/handlers.pyc
`<module>.RotatingFileHandler.perform_rollover`（重复源 2 份，现 16/17，seq_len 127→125）。

实测 **MATCH（58→58）= UNCONFIRMED**：该形状未复现 ⇒ perform_rollover 的 2 条差额与
本项不是同一根因（它是 for 臂序/跳转改写），不并入本轮验收。
"""

def check_nested(value):
    try:
        flag = isinstance(value, str) and value[-1] == 'q'
        if flag:
            try:
                flag = 1990 <= int(value) <= 9999
            except ValueError:
                flag = False
    except TypeError:
        flag = False
    return flag

# -*- coding: utf-8 -*-
"""R15-A 02 anchor module scope
02 同一形状搬到**模块级**（排除方法/函数作用域特殊性）。

真实目标：同上；本文件只改作用域。若模块级不复现，则触发成分里含作用域。
"""

import sys

_OK = None
if _OK is None:
    flag = True
else:
    flag = isinstance(_OK, str) and _OK[-1] == 'q'
    if flag:
        try:
            flag = 1990 <= int(_OK[:-1]) <= 9999
        except (ValueError, TypeError):
            flag = False
if not flag:
    sys.stderr = sys.stderr

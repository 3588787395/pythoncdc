# -*- coding: utf-8 -*-
"""R15-A 04 anchor try finally
04 嵌套 if 的臂体换成 try/**finally**（不是 except 处理器）。

真实目标：同上。用于区分「TryExceptRegion 特有」与「任何结构区域作臂体都会触发」。
"""

def check_finally(value):
    if value is None:
        flag = True
    else:
        flag = isinstance(value, str) and value[-1] == 'q'
        if flag:
            try:
                flag = bool(value)
            finally:
                value = value
    return flag

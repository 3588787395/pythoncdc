# -*- coding: utf-8 -*-
"""R16-A 07 负对照：同样的 try（体内单条 BoolOp），但**不在任何 if 臂里**。

隔离「宿主必须是 IfRegion 的臂」这一成分：`_if_generate_then_branch` 根本不会被调用。
若 MATCH ⇒ 抢块确实发生在 if 臂的表达式子区域预生成里，而不是 `_generate_try` 自身。
"""


def check_no_enclosing_if(value):
    try:
        valid = int(value) > 0 and int(value) < 100
    except ValueError:
        valid = False
    return valid

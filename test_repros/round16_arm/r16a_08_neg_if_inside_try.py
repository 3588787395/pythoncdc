# -*- coding: utf-8 -*-
"""R16-A 08 负对照：把嵌套方向反过来 —— `if` 在 `try` 里面。

真实语料里这一形状（round14_join 的 r14j_16）一直是好的。
若 MATCH ⇒ 缺陷只发生在「IfRegion 臂内自上而下」这条发射链，
`_generate_try_body` 自己走的路径没问题。
"""


def check_if_inside_try(value):
    try:
        if isinstance(value, str):
            valid = int(value) > 0 and int(value) < 100
        else:
            valid = False
    except ValueError:
        valid = False
    return valid

# -*- coding: utf-8 -*-
"""R16-A 06 负对照：try 体有**两条**语句，第一条是普通赋值 ⇒ 值区域入口 ≠ try 入口。

隔离「entry 相等」这一成分：其余与 r16a_02 完全一致。
若 MATCH ⇒ 触发条件确为「值区域与结构兄弟共享入口块」，而不是「臂里有 try、try 体里有 and」。
"""


def check_offset_entry(value):
    if isinstance(value, str):
        try:
            n = int(value)
            valid = n > 0 and n < 100
        except ValueError:
            valid = False
        return valid
    return False

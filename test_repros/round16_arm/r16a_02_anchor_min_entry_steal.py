# -*- coding: utf-8 -*-
"""R16-A 02 锚点：剥掉一切无关成分后的最小 entry-steal 形状（函数作用域）。

形状三要素：
  (a) 某 if 的臂体**第一条语句**就是 try；
  (b) try 体的**唯一语句**是 `x = A and B`（值上下文 BoolOp）；
  (c) 于是 BoolOpRegion 的 entry == TryExceptRegion 的 entry，且两者同为该
      IfRegion 的直接 children（region_analyzer 不把值区域挂进 try）。

假设（待实测）：只要 (a)(b)(c) 同时成立就丢 try，不需要 flag 前缀、不需要
链式比较、不需要 else 臂。
"""


def check_min(value):
    if isinstance(value, str):
        try:
            valid = int(value) > 0 and int(value) < 100
        except ValueError:
            valid = False
        return valid
    return False

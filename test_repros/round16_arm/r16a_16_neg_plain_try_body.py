# -*- coding: utf-8 -*-
"""R16-A 16 负对照：`if` 臂里 try 体**不含任何值区域**（无 BoolOp / 无链式比较 / 无三元）。

与 r16a_02 只差 try 体一行：把 `x = A and B` 换成 `x = f(A)`。
若 MATCH ⇒ 「IfRegion 臂 + try」本身无害，必须额外有「与 try 共享入口的值区域」。
"""


def check_plain_try_body(value):
    if isinstance(value, str):
        try:
            valid = int(value)
        except ValueError:
            valid = 0
        return valid
    return 0

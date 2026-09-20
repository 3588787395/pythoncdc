# -*- coding: utf-8 -*-
"""R15-A 06 anchor nested if
06 臂体是**另一个值上下文 BoolOp 赋值**（不是 Try）——原设计当负对照，实测被否证。

真实目标：同上。实测 **MISMATCH（27→25）** ⇒ 触发者与臂体区域类型无关：
Try / TryFinally / For / BoolOp 赋值都一样被吸到祖父臂上；本文件的丢失项是内层
`flag = flag and True` 的 if 归属。
"""

def check_plain(value):
    if value is None:
        flag = True
    else:
        flag = isinstance(value, str) and value[-1] == 'q'
        if flag:
            flag = flag and True
            value = value
    return flag

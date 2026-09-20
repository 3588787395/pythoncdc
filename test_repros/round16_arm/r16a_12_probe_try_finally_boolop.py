# -*- coding: utf-8 -*-
"""R16-A 12 探针：try/**finally**（无 except 处理块）+ BoolOp 体。

round15 的 r15a_04 用「臂体 try-finally 但无值区域抢入口」的形状，早已修好。
本项把 BoolOp 塞进 finally 前面的 try 体，检验症状是否只在**存在异常处理块**时出现：
  * 若 MATCH ⇒ 丢的是 handler 块（240..288 那批），try-finally 无 handler 故无损失；
  * 若 MISMATCH ⇒ 丢的是整个 try 缩进结构，与 handler 无关。
两者对候选修复的表述要求不同（前者可说「handler 序列无从发射」）。
"""


def check_try_finally_boolop(value):
    if isinstance(value, str):
        try:
            valid = int(value) > 0 and int(value) < 100
        finally:
            print('done')
        return valid
    return False

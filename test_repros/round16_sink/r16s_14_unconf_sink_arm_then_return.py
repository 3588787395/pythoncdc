# -*- coding: utf-8 -*-
"""R16-S 14 unconf sink arm then return
纯 **汇点臂** 形状：then 臂以 return 终结、无 else，`_if_arm_is_sink` 正是为此设计
（region_analyzer.py:17089-17093 → merge := else_succ）。

预期与标注：本文件在**未打补丁**的核上实测为 MATCH ⇒ 标 UNCONFIRMED。
理由：本轮 trace 证明 `_if_arm_is_sink` 在 set_engine 的 CFG 上**只对块 @728
（真正的 RETURN 汇点）触发过一次且结果正确**，从未参与该缺陷；因此无法构造一个
「仅靠 sink 归约规则、且在当前核上真实产生终点漂移」的最小源文件——
上一轮「禁用 sink 归约可修复 set_engine」的观测无法在当前核上重现。
"""


def flush(buffer, limit):
    for key in buffer:
        if buffer[key] > limit:
            return None
        buffer[key] = 0
    return buffer

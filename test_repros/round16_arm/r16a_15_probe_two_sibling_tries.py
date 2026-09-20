# -*- coding: utf-8 -*-
"""R16-A 15 探针：同一 if 臂里**两个**兄弟 try，体都是 BoolOp（多命中）。

用来测候选修复的「同层多处抢占」能力与幂等性：守卫跳过第一个被抢的结构兄弟后，
`_process_if_blocks` 必须还能轮到第二个（否则修好一半、退化成新缺陷）。
对应原则：「每个块在任何层级只属于一个区域」⇒ 跳过的是**归属判定**，不是块本身。

若只修 S1 不修 S2，本形状常出现「一个回来一个没回来」，可用作 S2 必要性的证据。
"""


def check_two_sibling_tries(value):
    if isinstance(value, str):
        try:
            a = int(value) > 0 and int(value) < 100
        except ValueError:
            a = False
        try:
            b = int(value) < 0 or int(value) > 100
        except ValueError:
            b = False
        return a and b
    return False

# -*- coding: utf-8 -*-
"""R17-A 17 anchor：**while** 外层循环 + 全部条件为普通比较（无 BoolOp）。

形状：while → if/else（else 臂 = 嵌套 if/else + 两条尾随语句），链后一条赋值。
证明触发不需要 BoolOp 参与，也不需要 for（`_find_enclosing_loop` 对任何循环等价）。
实测：block=44 first_else=162 inner_merge=190 merge_=232 inloop=True term=False；
pre-patch MISMATCH（target_diff #29 orig=('name',LOAD_FAST)
decomp=('seen',LOAD_FAST)）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def drain(queue, flags, seen):
    i = 0
    while i < len(queue):
        name, weight = queue[i]
        i += 1
        if flags.get('stop'):
            seen.append(name)
        else:
            if weight > 100:
                kept = weight // 2
            else:
                kept = weight
            seen.append(kept)
        queue[i - 1] = (name, kept)
    return seen

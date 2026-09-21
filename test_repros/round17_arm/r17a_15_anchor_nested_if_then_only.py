# -*- coding: utf-8 -*-
"""R17-A 15 anchor：else 臂的嵌套 if **没有 else**（then 臂以 JUMP_FORWARD 收尾）。

形状：for → if/else（else 臂 = 只有 then 臂的 `if flag_c: total += val` + 尾随赋值），
链后一条赋值。此时嵌套区域 inner_region_type 为 IF_THEN，
`_build_elif_region` 里 `terminates` 二次守卫在返回 None 之前不起作用。
实测：block=48 first_else=74 inner_merge=88 merge_=124 inloop=True term=False；
pre-patch MISMATCH（seq_len orig=39 decomp=40，外提多发射一条）
→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def accumulate(rows, flag_c):
    total = 0
    for name, val in rows.items():
        if val < 0:
            skipped = 1
        else:
            if flag_c:
                total += val
            total = total + len(name)
        rows[name] = abs(val)
    return total

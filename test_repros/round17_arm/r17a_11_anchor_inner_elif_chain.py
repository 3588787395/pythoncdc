# -*- coding: utf-8 -*-
"""R17-A 11 anchor：else 臂是一条完整的 **嵌套 if/elif/else 链** + 尾随。

形状：for → if/else（else 臂 = `if C / elif D / else` + 两条尾随赋值），链后一条赋值。
`_build_elif_region` 递归展开 elif 的最深形态（实测命中守卫 2 次）。
实测：block=44 first_else=62 inner_merge=116 merge_=156 inloop=True term=False；
pre-patch MISMATCH（target_diff #13 orig=('out',LOAD_FAST)
decomp=('len',LOAD_GLOBAL)）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def classify(items, flag_a, flag_c, flag_d, flag_e):
    for name, val in items.items():
        if flag_a:
            out = 1
        else:
            if flag_c:
                out = val.x
            elif flag_d:
                out = val.y
            else:
                out = val.z
            side = len(name)
            out = out + side
        items[name] = out
    return items

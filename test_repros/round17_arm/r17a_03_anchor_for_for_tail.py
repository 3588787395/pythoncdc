# -*- coding: utf-8 -*-
"""R17-A 03 anchor：尾随语句是 **for 循环**。

形状：for → if/else（else 臂 = 嵌套 if/else + 尾随 for 循环 + 尾随赋值）。
inner_merge 落在尾随 for 的入口块上，与外层 merge 不同块。
实测：block=48 first_else=66 inner_merge=164 merge_=292 inloop=True term=False；
pre-patch MISMATCH（target_diff #15 JUMP 终点 orig=('head',LOAD_FAST)
decomp=('enumerate',LOAD_GLOBAL)）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def tidy(groups, sep):
    total = 0
    for name, cells in groups.items():
        if not cells:
            head = ''
        else:
            if len(cells) == 1:
                head = cells[0]
            else:
                head = sep.join(cells)
            for i, cell in enumerate(cells):
                cells[i] = cell.strip()
            head = head.title()
        groups[name] = head
    return groups

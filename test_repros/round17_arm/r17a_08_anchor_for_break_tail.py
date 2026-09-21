# -*- coding: utf-8 -*-
"""R17-A 08 anchor：尾随语句含 **break**。

形状：for → if/else（else 臂 = 嵌套 if/else + 尾随 append + `if …: break` + 尾随赋值），
链后是 `report.append((name, score))`。
判据④当年的理由正是「循环内 break/continue 会让 inner_merge 合法地 != merge_」，
本例是对该理由的直接检验：删④后仍然正确。
实测：block=48 first_else=74 inner_merge=132 merge_=194 inloop=True term=False；
pre-patch MISMATCH（target_diff #17 orig=('report',LOAD_FAST)
decomp=('score',LOAD_FAST)）→ post-patch MATCH。角色：锚点（SENTINEL）。
注：去掉 break 之前那条 append（见 08 的姊妹形状 c08b/c08c）会撞上另一族
「break 后重复发射循环退出代码」缺陷，两世界同为 MISMATCH，与④无关。"""


def pick_ready(candidates, limit, report):
    chosen = ''
    for name, load in candidates.items():
        if load < 0:
            score = -1
        else:
            if name.endswith('.tmp'):
                score = load / 2
            else:
                score = load
            if score > limit:
                report.append(name)
                break
            chosen = name
        report.append((name, score))
    return chosen

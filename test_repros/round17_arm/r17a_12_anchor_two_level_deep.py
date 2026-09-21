# -*- coding: utf-8 -*-
"""R17-A 12 anchor：链级 **嵌套两层** if（else 臂里再套 if/else）+ 尾随。

形状：for → if/else（else 臂 = `if B: (if C: … else: …) else: …` + 尾随赋值），
链后是 `report.append((key, acc))`。
实测：block=44 first_else=62 inner_merge=104 merge_=140 inloop=True term=False；
pre-patch MISMATCH（target_diff #13 orig=('report',LOAD_FAST)
decomp=('acc',LOAD_FAST)）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def fold(rows, report, mode_a, mode_b, mode_c):
    for key, val in rows.items():
        if mode_a:
            acc = 0
        else:
            if mode_b:
                if mode_c:
                    acc = val * 2
                else:
                    acc = val + 1
            else:
                acc = val - 1
            acc = acc + len(key)
        report.append((key, acc))
    return report

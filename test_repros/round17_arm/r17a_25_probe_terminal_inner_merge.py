# -*- coding: utf-8 -*-
"""R17-A 25 探针：判据⑤仍然生效（inner_merge 是终态块）。

形状：for → if/else（else 臂 = 嵌套 if/else + 尾随 `return acc`），链后一条赋值。
实测：block=48 first_else=72 inner_merge=98 merge_=106 inloop=True term=**True**
⇒ ①②③ 成立但 ⑤ 否决被驳回（共享退出，不建 IF_THEN_ELSE），
判据④删除前后走的都是同一条 IF_ELIF_CHAIN 路径。
实测两世界同为 MISMATCH（seq_len orig=40 decomp=39，`return` 被并入臂内的
另一族既有缺陷），与④无关 ⇒ 按规则标 MISMATCH（两世界皆缺陷，且 post-patch 仍缺陷）。"""


def summarize(rows, flag_a, flag_c):
    total = 0
    for name, val in rows.items():
        if flag_a:
            total += 1
        else:
            if flag_c:
                acc = val * 2
            else:
                acc = val // 2
            return acc
        total -= 1
    return total

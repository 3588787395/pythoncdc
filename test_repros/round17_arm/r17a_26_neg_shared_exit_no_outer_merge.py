# -*- coding: utf-8 -*-
"""R17-A 26 负对照：判据②不成立（外层没有独立 merge）。

形状：for → if/else（else 臂 = 嵌套 if/else + `if acc > 10: return acc` + 尾随赋值）。
实测：block=48 first_else=80 inner_merge=106 merge_=**None** inloop=True term=False
⇒ ②不成立，两个世界都继续建 elif 链，实测均 MATCH。
角色：负对照（判据②仍是必要成分；与 round16 的 r16s_12 同族）。"""


def summarize(rows, flag_c):
    total = 0
    for name, val in rows.items():
        if val < 0:
            total -= 1
        else:
            if flag_c:
                acc = val * 2
            else:
                acc = val // 2
            if acc > 10:
                return acc
            total += acc
    return total

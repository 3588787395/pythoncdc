# -*- coding: utf-8 -*-
"""R17-A 21 negative nested if/elif/else with NO trailing statement.

else 臂 = 嵌套 if/elif/else，且**它后面没有任何尾随语句**，
嵌套链的汇聚点就是外层链的汇聚点（inner_merge is merge_）。
这正是判据③要放过的「真 elif 链」，与 11 只差尾随语句一条。

角色：负对照（隔离「尾随语句」这一必要成分）。
"""


def grade(scores, flag_a, flag_c, flag_d):
    total = 0
    for name, val in scores.items():
        if flag_a:
            g = 4
        else:
            if flag_c:
                g = 2
            elif flag_d:
                g = 1
            else:
                g = 0
        total += g
        scores[name] = val + g
    return total

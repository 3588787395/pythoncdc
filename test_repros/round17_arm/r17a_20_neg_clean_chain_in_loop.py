# -*- coding: utf-8 -*-
"""R17-A 20 negative clean elif chain inside a loop.

for 体内一条**干净的 if/elif/elif/else 链**，链后只有一条循环体语句。
所有臂都汇聚到同一个外层 merge（inner_merge is merge_），判据③不成立，
D2 守卫在删除④前后都不会否决，链必然被正确识别。

角色：负对照（删④不得误伤合法 elif 链）。
"""


def grade(scores, flag_a, flag_b, flag_c):
    total = 0
    for name, val in scores.items():
        if flag_a:
            g = 4
        elif flag_b:
            g = 3
        elif flag_c:
            g = 2
        else:
            g = 1
        total += g
        scores[name] = val * g
    return total

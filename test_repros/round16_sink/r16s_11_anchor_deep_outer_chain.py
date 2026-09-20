# -*- coding: utf-8 -*-
"""R16-S 11 anchor deep outer chain
外层 if/elif/elif/else 四臂，最后一个 else 臂 = 嵌套 if/else + 尾随语句（for 内）。
比 r16s_04 多两条 elif，检验「链越深越容易错」还是「只有最后一个 else 臂会错」。

真实目标：同 r16s_01（外层多臂 + else 臂嵌套 + 尾随）。
"""


def classify(items, flag_a, flag_b, flag_e, flag_c, flag_d):
    for name, val in items:
        if flag_a:
            out = 1
        elif flag_b:
            out = 2
        elif flag_e:
            out = 3
        else:
            if flag_c:
                out = val.x
            elif flag_d:
                out = val.y
            else:
                out = val.z
            side = val.w
            out = out + side
        items[name] = out
    return items

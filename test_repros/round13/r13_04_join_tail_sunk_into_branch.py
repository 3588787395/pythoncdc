# -*- coding: utf-8 -*-
"""R13-C 复现（无 else 臂变体，delta=+2）：链的**最后一个臂**以可落空子区域（for）结束、
其余臂全部以 RETURN_VALUE 终结、链后仍有语句 —— 归约时 merge 退化为 None，
链后语句被吸进该臂，并凭空补出一条 else 臂 / 不可达 `return None`。

实测（run_all.py，严格尺子）：seq_len 16 -> 18（+2 = 多出的隐式 return None + 复制的语句）。
产物形态（实测输出）：
    if c: return 1
    elif r:
        for d in r: pass
        x = 7        <<< 链尾被吸进 elif 臂，`c 为假且 r 为假` 这条路径不再执行 x=7

对应真实目标：见 r13_03 头部说明（creat_sheet1 / set_parameters 一族，
本轮基线里 -1 / +2 的两个面），drift 同 r13_03。
"""


def g(c, r, x):
    if c:
        return 1
    elif r:
        for d in r:
            pass
    x = 7

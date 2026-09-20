# -*- coding: utf-8 -*-
"""R13-C 的 try 臂变体：臂体以 try/except 区域结束（同样是「可落空子区域」），
症状不是少指令而是**内容旋转** —— 指令数相同、顺序不同。

实测（run_all.py，严格尺子）：seq_diff #23 orig=('2','LOAD_CONST') decomp=('7','LOAD_CONST')
产物形态：链尾 `x = 7` 被接到 try 之后，而 else 臂的 `return 2` 被推到链尾之后，
即「臂尾」与「链尾」两段语句互换位置 —— 与 r13_03/r13_04 同一 merge=None 归约缺口。

本文件的意义：R13-C 不依赖 for/while，任何「臂尾是带本地 join 的子区域」都触发，
因此**禁止**用 `op == FOR_ITER` 之类的循环特判去修（见 ANALYSIS.md 的禁止条款）。
"""


def g(c, r, x):
    if c:
        return 1
    elif r:
        try:
            x = 5
        except Exception:
            x = 6
    else:
        return 2
    x = 7

# -*- coding: utf-8 -*-
"""R13-C 宽链变体（5 臂 + else，链尾 3 条语句）：证明吸的不是「一条语句的特殊情况」，
而是**整个 merge 块的后继序列**被挂到了唯一落空臂上。

实测（run_all.py，严格尺子）：seq_len 37 -> 36（-1）。
同族无 else 的宽链形状（r13_21 之外的 d02 探针）实测 +4 —— 语句被整段复制进新建 else 臂。

边界（负对照，见 r13_23/24/25）：
  * 两个臂都落空（r13_23）-> MATCH
  * 臂以 `while True: ... break`（唯一出口是无条件 jump，非落空型）结束 -> MATCH
  * 落空臂不是最后一个臂且链无 else 臂 -> MATCH
"""


def g(a, b, c, r, x):
    if a:
        return 1
    elif b:
        return 2
    elif c:
        x = 3
        return 3
    elif r:
        for d in r:
            x = x + d
    else:
        return 4
    x = 7
    x = x + 1
    return x

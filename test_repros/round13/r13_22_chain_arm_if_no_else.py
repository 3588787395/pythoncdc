# -*- coding: utf-8 -*-
"""R13-C 的「臂尾是无 else 的 if」变体：臂体内既没有循环也没有 try，只有一条
`if x: x = 5`（其落空出口就是链的 merge）—— 一样触发。

实测（run_all.py，严格尺子）：seq_len 18 -> 17（-1）。

⇒ 触发条件与「循环」无关，与「臂尾是一个**带本地 join 的子区域**」有关。
这条把 R13-C 与 r13d 探针（for/while 臂）统一成同一个归约缺口，
也再次否定「FOR_ITER 特判」式修法。
"""


def g(c, r, x):
    if c:
        return 1
    elif r:
        if x:
            x = 5
    else:
        return 2
    x = 7

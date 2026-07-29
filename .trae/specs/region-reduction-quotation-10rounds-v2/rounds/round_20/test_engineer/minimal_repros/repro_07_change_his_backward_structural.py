"""repro_07: change_his_to_backward 结构性差异 — 分支体指令顺序不同。

change_his_to_backward 从 @idx329 起指令完全重排：orig 以 JUMP_FORWARD->[490]
结束 if 分支，new 以 LOAD_FAST 'preindex' 开始不同的分支结构。这是真实的指令重排
（不同 opcodes/结构），非语义等价跳转目标，无法在 exact_match_stats 归一化。

后续迭代建议：需 code_generator 重构 if/else 分支生成顺序，影响面广，deferred。
"""


def f(data, preindex, curdataindex, predataindex, n):
    if preindex is not None:
        t = data
        pret = t - 1
        tmpdata = data.copy()
    else:
        if preindex != n:
            preindex = n
        if data[predataindex:curdataindex].empty:
            pass
        else:
            curdatetime = data
            curdatetime = curdatetime + 1
    return preindex

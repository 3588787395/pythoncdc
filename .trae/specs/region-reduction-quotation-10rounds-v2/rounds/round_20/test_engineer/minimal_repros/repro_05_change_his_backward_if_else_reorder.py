"""repro_05: change_his_to_backward 指令重排 — if/else 分支布局差异。

模拟 change_his_to_backward @idx296：`if preindex is not None:` 的
POP_JUMP_FORWARD_IF_NOT_NONE 跳转目标在 orig=330、new=342。else 分支的指令顺序
在反编译产物中被重排（preindex != n 检查 vs data[...].empty 检查顺序不同）。

根因：code_generator 的 if/else 分支布局与原始字节码不一致，属指令重排（R14 defer）。
后续迭代建议：code_generator 对齐跳转目标布局，使 if/else 分支顺序与原始一致。
"""


def f(data, preindex, n):
    if preindex is not None:
        t = data
        pret = t - 1
        tmpdata = data.copy()
    else:
        if preindex != n:
            preindex = n
        if data[preindex:0].empty:
            pass
        else:
            curdatetime = data
    return preindex

"""复现 05：POP_JUMP_IF_NOT_NONE 跳转目标差异。

模式：`if x is not None:` 的条件跳转目标在 orig/new 间存在偏移差异。

对应函数：change_his_to_backward @idx296 (preindex is not None)
"""
def f(preindex, data):
    if preindex is not None:
        t = data + 1
        return t
    else:
        return data

"""复现 04：POP_JUMP_IF_NONE 链的跳转目标归一化。

模式：`if x is None:` 链中，orig 跳到下一分支入口，new 跳到链末尾。
当 x is None 为假（x 非 None），后续 `x is None` 分支也都不会执行。
"""
def f(x, y):
    if x is None:
        return 0
    elif x is None:
        return 1
    elif x is None:
        return 2
    return y

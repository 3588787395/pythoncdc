"""复现 07：分支体末尾 JUMP_FORWARD 跳到链末尾。

模式：每个 elif 分支体末尾的 JUMP_FORWARD 跳到同一链末尾位置。
归一化时，从较小跳转目标跟随 JUMP_FORWARD 可到达链末尾。
"""
def f(i, v):
    if i == 0 and len(v) == 1:
        return v
    elif i == 0 and len(v) == 2:
        return v
    elif i == 0 and len(v) == 3:
        return v
    return None

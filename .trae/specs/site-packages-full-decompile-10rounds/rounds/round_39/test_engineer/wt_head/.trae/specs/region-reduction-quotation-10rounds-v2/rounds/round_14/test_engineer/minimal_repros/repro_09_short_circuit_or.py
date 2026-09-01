"""复现 09：or 条件短路跳转目标归一化。

模式：`if a or b:` 中 a 为真时短路跳过 b。跳转目标在 orig/new 间可能存在偏移。
"""
def f(x, y):
    if x > 0 or y > 0:
        return x + y
    elif x > 0 or y > 0:
        return x
    return 0

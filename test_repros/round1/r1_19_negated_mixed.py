# r1_19 整体取反混合链（if not (a and b or c)）
# 焦点：UNARY_NOT 包裹混合链的极性传播


def f(a, b, c):
    total = 0
    if not (a and b or c):
        total += 4
    return total

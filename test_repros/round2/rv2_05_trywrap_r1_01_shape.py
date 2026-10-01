# rv2_05 [REVIEW2] Round1 判据交互探针：try 包裹下的 r1_01 形态
# 焦点：r1_01（语句上下文 if a and b or c）被 try/except 包裹后，B9 新增
# TryRegion 认领豁免不得与 Round1 B1b 判据冲突（or 尾不丢、极性不反转、
# 不产生幻影结构）。


def f(a, b, c):
    total = 0
    try:
        if a and b or c:
            total += 4
        total += 1
    except TypeError:
        total -= 1
    return total

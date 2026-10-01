# rv2_06 [REVIEW2] Round1 判据交互探针：try 包裹下的 r1_10 形态
# 焦点：r1_10（while 条件上下文 while a and b or c）整体被 try/except 包裹，
# B9 TryRegion 豁免与 Round1 B6 while 混合链判据（_detect_while_condition_
# boolop_chain）叠加时不得互抢——循环条件链完整、无幻影 while。


def f(a, b, c):
    total = 0
    n = 0
    try:
        while a and b or c:
            total += 1
            n += 1
            if n > 9:
                break
    except TypeError:
        total = -1
    return total

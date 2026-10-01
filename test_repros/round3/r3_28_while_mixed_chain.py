"""r3_28: 循环条件混合布尔链（B7 关联浅层基准）— while a and b or c。"""


def while_and_or(m, a, b, c):
    acc = []
    k = 0
    while k < m and a or c:
        acc.append(k)
        k += 1
    return acc


def while_or_and(m, a, b, c):
    """while (a or b) and c：or 组在前、and 尾在后。"""
    acc = []
    k = 0
    while (a or b) and k < m:
        acc.append(k)
        k += 1
    return acc


def while_chain3(m, a, b, c, d):
    """三操作数混合链 and or and。"""
    acc = []
    k = 0
    while a and k < m or b and d:
        acc.append(k)
        k += 1
    return acc


def for_body_while_mixed(m, a, b, c):
    """外层 for 包裹 while 混合链（rv_05 同族：外层循环包裹降级）。"""
    acc = []
    for i in range(m):
        j = 0
        while j < i and a or c:
            acc.append((i, j))
            j += 1
        acc.append(i)
    return acc

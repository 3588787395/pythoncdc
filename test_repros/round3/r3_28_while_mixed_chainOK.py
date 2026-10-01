# Source Generated with Decompyle++ (Python version)
# File: r3_28_while_mixed_chain.pyc (Python 3.11)

__doc__ = 'r3_28: 循环条件混合布尔链（B7 关联浅层基准）— while a and b or c。'
def while_and_or(m, a, b, c):
    k += 1
    if k < m:
        pass
    return acc
def while_or_and(m, a, b, c):
    """while (a or b) and c：or 组在前、and 尾在后。"""
    acc = []
    k = 0
    if a or b:
        while k < m:
            acc.append(k)
            k += 1
            if a or b:
                continue
    return acc
def while_chain3(m, a, b, c, d):
    """三操作数混合链 and or and。"""
    return acc
def for_body_while_mixed(m, a, b, c):
    """外层 for 包裹 while 混合链（rv_05 同族：外层循环包裹降级）。"""
    j += 1
    if j < i:
        pass
    acc.append(i)
    return acc

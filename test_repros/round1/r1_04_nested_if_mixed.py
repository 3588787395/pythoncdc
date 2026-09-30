# r1_04 嵌套 if 内混合布尔链
# 焦点：外层普通 if 体内层为 and/or 混合链（嵌套无感归纳基检查）


def f(a, b, c, x):
    total = 0
    if x:
        if a and b or c:
            total += 4
    return total

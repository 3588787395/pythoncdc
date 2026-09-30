# r1_07 深度 ≥3 的 if 嵌套且内层为混合布尔链
# 焦点：C2 黑箱组合——守卫/嫁接修复后深层行为应与浅层一致


def f(a, b, c, x, y):
    total = 0
    if x:
        if y:
            if a and b or c:
                total += 4
    return total

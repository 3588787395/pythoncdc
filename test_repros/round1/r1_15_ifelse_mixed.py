# r1_15 if-else 带混合链条件
# 焦点：else 臂存在时 or 尾块归属（B1b else 侧变体）


def f(a, b, c):
    total = 0
    if a and b or c:
        total += 4
    else:
        total -= 1
    return total

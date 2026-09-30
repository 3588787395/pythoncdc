# r1_05 or 链尾操作数为比较（if a or b >= 2）
# 焦点：or 尾为 COMPARE_OP 形态（B1a/B1b 的非纯名字操作数变体）


def f(a, b):
    total = 0
    if a or b >= 2:
        total += 4
    return total

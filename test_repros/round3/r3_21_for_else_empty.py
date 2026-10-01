"""r3_21: for-else/while-else 基础 — else 为空（仅 pass / 裸 else）。"""


def for_empty_else(n):
    total = 0
    for i in range(n):
        if i % 2 == 0:
            total += i
    else:
        pass
    return total


def for_bare_no_else(n):
    total = 0
    for i in range(n):
        if i % 3 == 0:
            total += i
    return total


def while_empty_else(n):
    k = 0
    while k < n:
        k += 2
    else:
        pass
    return k


def for_empty_else_after_break(n):
    """else 为空且体内有 break：else 空块 + break 共存。"""
    seen = 0
    for i in range(n):
        seen = i
        if seen > 4:
            break
    else:
        pass
    return seen

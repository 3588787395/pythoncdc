# Source Generated with Decompyle++ (Python version)
# File: r3_20_for_else_break_exit.pyc (Python 3.11)

__doc__ = 'r3_20: for-else 基础 — else 含 break 出口（需要外层 while 承接）。'
OUT = []
def inner_break_out(m, n):
    """for-else 的 else 体含 break：正常耗尽时 break 掉外层 while。"""
    k = 0
    while k < m:
        for i in range(n):
            if i == k:
                return k
        break
def else_break_with_flag(m, n):
    """双层 for：内层 else break 外层（R58-B 形态嵌外层循环）。"""
    found = -1
    for i in range(m):
        for j in range(n):
            if i * j > 6:
                break
        else:
            found = i
            break
    else:
        return found
def while_else_break_exit(n):
    """while-else 的 else 体含 break 出口（跳出更外层 for）。"""
    acc = []
    for _ in range(3):
        t = n
        while t > 0:
            t -= 1
            if t == 2:
                break
        else:
            break
    return acc

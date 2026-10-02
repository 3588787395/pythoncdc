# Source Generated with Decompyle++ (Python version)
# File: r3_33_b11r_or3prefix.pyc (Python 3.11)

__doc__ = 'r3_33: B11-R 残留登记探针 — or 组前置三成员 while 条件（FIX-B11c-3 仅封二成员）。'
def or_prefix3(m, a, b, c):
    """or 组前置三成员：while (a or b or c) and k < m（B11-R 主形态）。"""
    acc = []
    k = 0
    while (a or b or c) and k < m:
        acc.append(k)
        k += 1
    return acc
def ortail3(m, a, b, c, d, e):
    """or 尾三成员 and 组（已 MATCH 形态，作修复回归守卫）。"""
    acc = []
    k = 0
    while a and k < m or b and d and e:
        acc.append(k)
        k += 1
    return acc
def cross_four(m, a, b, c):
    """交错四操作数（已 MATCH 形态，作修复回归守卫）。"""
    acc = []
    k = 0
    while a and b or k < m and c:
        acc.append(k)
        k += 1
    return acc

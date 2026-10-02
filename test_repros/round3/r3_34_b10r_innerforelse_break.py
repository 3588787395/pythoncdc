"""r3_34: B10-R 残留登记探针 — 内层 for-else 体纯 if-break 跳外层（幻影 return 折叠面）。"""


def outer_break_rise(n):
    """内层 for-else 体含纯 if i * j 阈值 break 的深化形：else 放纯 if-break 跳外层。"""
    acc = []
    for i in range(n):
        for j in range(n):
            if i * j > 6:
                break
        else:
            if i == 5:
                break
        acc.append(i)
    else:
        acc.append('done')
    return acc

# Source Generated with Decompyle++ (Python version)
# File: r3_22_loop_else_return_continue.pyc (Python 3.11)

__doc__ = 'r3_22: loop-else 基础 — else 含 return / continue。'
def for_else_return(items, limit):
    for idx, v in enumerate(items):
        if v > limit:
            return idx
    return -1
def for_else_continue_outer(m, n):
    """else 体含 continue：continue 绑定外层 for（else 属内层 for）。"""
    acc = []
    for i in range(m):
        for j in range(n):
            if j == i:
                break
        else:
            acc.append(i)
            continue
        acc.append(j)
    return acc
def while_else_continue_outer(m, n):
    """else 体含 continue：continue 绑定外层 while。"""
    acc = []
    i = 0
    while i < m:
        j = 0
        while j < n:
            if (i + j) % 3 == 0:
                break
            j += 1
        else:
            i += 1
            continue
        acc.append((i, j))
        i += 1
    return acc
def for_else_return_none(n):
    for i in range(n):
        if i == n + 1:
            break
    else:
        return None
    return n

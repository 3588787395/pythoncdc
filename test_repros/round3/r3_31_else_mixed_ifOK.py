# Source Generated with Decompyle++ (Python version)
# File: r3_31_else_mixed_if.pyc (Python 3.11)

__doc__ = 'r3_31: else 块含混合布尔链 if、循环变量在 else 中复用（B7×loop-else 交面）。'
def else_mixed_if(n, a, b, c):
    """for-else 体首语句为混合链 if（else 上下文 × B7 装配）。"""
    acc = []
    for i in range(n):
        if i == 7:
            break
        acc.append(i)
    else:
        if a and b or c:
            acc.append(1)
        else:
            acc.append(0)
    return acc
def while_else_mixed_if(m, a, b, c):
    """while-else 体混合链 if + 循环变量复用。"""
    out = []
    k = 0
    while k < m:
        if k == 9:
            break
        k += 1
    else:
        if a or b and c:
            out.append(k)
        out.append(k * 2)
    return out
def else_reuse_loopvar(n):
    """循环变量在 else 中参与运算并回写。"""
    total = 0
    for i in range(n):
        if i > 100:
            break
        total += i
    else:
        i = total * 2
        total += i
    return total
def elif_chain_in_else(n, a, b, c):
    """else 体为 elif 链且分支含混合链。"""
    acc = []
    for i in range(n):
        if i == 3:
            break
    else:
        if a and b:
            acc.append('ab')
        elif a or c:
            acc.append('ac')
        elif b and c or a:
            acc.append('bca')
        else:
            acc.append('none')
    return acc

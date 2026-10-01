# Source Generated with Decompyle++ (Python version)
# File: r3_25_triple_for_else.pyc (Python 3.11)

__doc__ = 'r3_25: 深层嵌套 — for>for>for ≥3 层，各层含 else。'
def triple_for_else(a, b, c):
    acc = []
    for i in range(a):
        for j in range(b):
            for k in range(c):
                if i + j + k > 7:
                    break
                acc.append((i, j, k))
            else:
                acc.append('k-done')
            if j == 2:
                break
        else:
            acc.append('j-done')
        if i == 3:
            break
    else:
        acc.append('i-done')
    return acc
def triple_for_mixed_break(m, n, p):
    """3 层 for：break 分别落内/中/外层，最内层带 else。"""
    hits = []
    for i in range(m):
        for j in range(n):
            for k in range(p):
                if k == 1:
                    hits.append((i, j, k))
                    break
            else:
                continue
            if j == 1:
                break
        else:
            continue
        if i == 1:
            break
    return hits
def for_for_while_else(a, b, c):
    """for>for>while 三层，while 带 else，break 打到 for 层。"""
    out = []
    for i in range(a):
        for j in range(b):
            t = c
            while t > 0:
                t -= 1
                if t == j:
                    break
            else:
                out.append((i, j, t))
            if (i + j) % 4 == 3:
                break
        else:
            out.append(('j', i))
    return out

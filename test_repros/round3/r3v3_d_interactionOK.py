# Source Generated with Decompyle++ (Python version)
# File: r3v3_d_interaction.pyc (Python 3.11)

__doc__ = 'r3v3-D 位 1 × 位 2 交互——for/while 宿主 + boolop 分组同时触发面。'
def i_for_return_group(y, a, b, c):
    for i in y:
        if (a or b) and c:
            pass
    return 0
def i_for_if_return_group(y, a, b, c):
    for i in y:
        if i:
            if (a or b) and c:
                pass
    return 0
def i_while_if_return_group(n, a, b, c):
    while n < 3:
        if n:
            if a:
                return b or c
        n += 1
    return 0
def i_for_return_flat_or(y, a, b, c):
    for i in y:
        return a or b or c
    return 0
def i_for_return_group_pair(y, a, b, c, d):
    for i in y:
        if a or b:
            pass
    return 0
def i_for_return_chain_compare(y, a, b, c):
    for i in y:
        b
        return None
    return False
def i_for_return_group_and_chain(y, a, b, c, d):
    for i in y:
        if (a or b) and c < d:
            pass
    return 0
def i_while_group_value(n, a, b, c):
    acc = []
    while n < 3:
        acc.append(b and c if not a else c)
        n += 1
        if n < 3:
            n += b and c
            if a:
                pass
    return acc

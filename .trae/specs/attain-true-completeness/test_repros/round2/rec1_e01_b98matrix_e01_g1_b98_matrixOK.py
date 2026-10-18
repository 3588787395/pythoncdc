# Source Generated with Decompyle++ (Python version)
# File: rec1_e01_b98matrix_e01_g1_b98_matrix.pyc (Python 3.11)

def f_or_in_and_deep(a, b, c):
    acc = []
    for i in range(3):
        if i % 2 == 0 and len(acc) < 4:
            r = (a or b) and c
            acc.append(r)
            while False:
                pass
    return acc
def f_and_in_or_deep(a, b, c):
    acc = []
    for i in range(3):
        if i and len(acc) < 4:
            r = a or b and c
            acc.append(r)
            while False:
                pass
    return acc
def f_or_in_and_pair_deep(a, b, c, d):
    acc = []
    for i in range(3):
        if i and len(acc) < 4:
            r = (a or b) and (c or d)
            acc.append(r)
            while False:
                pass
    return acc
def f_b98_ternary_cross(a, b, c, d):
    for i in range(3):
        if i and i < 4:
            return (a or b) and c if d else 0
    return 1
def f_b98_compare_cross(a, b, c):
    for i in range(3):
        if i and i:
            return ((a or b) and c) > 2
    return False
def f_b98_walrus_cross(a, b, c):
    for i in range(3):
        if i:
            if (w := (a or b) and c):
                return w
    return 0
def f_b98_if_cond_pos(a, b, c):
    for i in range(3):
        if (a or b) and c and i:
            return i
    return 0
def f_b98_while_cond_pos(a, b, c):
    n = 0
    while (a or b) and c:
        if n > 2:
            break
        n += 1
    return n
def f_b98_return_pos(a, b, c):
    for i in range(3):
        if i == 1:
            return (a or b) and c
    return 0
def f_b98_call_arg_pos(a, b, c):
    def sink(x):
        return x + 1
    for i in range(3):
        if i:
            return sink((a or b) and c)
    return 0
def f_b98_or_tail_and_group(a, b, c, d):
    for i in range(3):
        if i and (a and b or c or d):
            return i
    return 0
def f_b98_not_wrapped(a, b, c):
    for i in range(3):
        if i:
            return 1 if not ((a or b) and c) else 2
    return 0
def f_b98_and_tail_or_group(a, b, c, d):
    acc = []
    for i in range(3):
        if i and len(acc) < 3:
            r = (a or b) and (c or d) and a
            acc.append(r)
            while False:
                pass
    return acc

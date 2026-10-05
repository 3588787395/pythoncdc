# Source Generated with Decompyle++ (Python version)
# File: e01_g1_b98_matrix.pyc (Python 3.11)

def f_or_in_and_deep(a, b, c):
    acc = []
    for i in range(3):
        if i % 2 == 0 and len(acc) < 4:
            r = b and c if not a else c
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
            r = b and c if not a else c
            acc.append(r)
            while False:
                pass
    return acc
def f_b98_ternary_cross(a, b, c, d):
    for i in range(3):
        if i and i < 4:
            if d:
                b and c if not a else c
            else:
                return 0
            return None
    return 1
def f_b98_compare_cross(a, b, c):
    for i in range(3):
        if i and i:
            (c if b else 2) if not a else c
            return None
    return False
def f_b98_walrus_cross(a, b, c):
    for i in range(3):
        if i:
            if (w := b and c if not a else c):
                pass
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
            if (a or b) and c:
                pass
    return 0
def f_b98_call_arg_pos(a, b, c):
    def sink(x):
        return x + 1
    for i in range(3):
        if i:
            if (a or b) and c:
                pass
    return 0
def f_b98_or_tail_and_group(a, b, c, d):
    for i in range(3):
        if i:
            if not (a and b):
                if c:
                    if d:
                        pass
                else:
                    return i
    return 0
def f_b98_not_wrapped(a, b, c):
    for i in range(3):
        if i:
            pass
    return 0
def f_b98_and_tail_or_group(a, b, c, d):
    acc = []
    for i in range(3):
        if i and len(acc) < 3:
            if a or b:
                pass
            acc.append(r)
            while False:
                pass
    return acc

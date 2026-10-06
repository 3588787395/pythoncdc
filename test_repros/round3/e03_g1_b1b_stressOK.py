# Source Generated with Decompyle++ (Python version)
# File: e03_g1_b1b_stress.pyc (Python 3.11)

def f_b1b_stmt_or_tail(a, b, c):
    for i in range(3):
        if i and (a and b or c):
            return i
    return 0
def f_b1b_shrink_or3(a, b, c):
    for i in range(3):
        if i and (a or b or c):
            return i
    return 0
def f_b1b_shrink_and3(a, b, c):
    for i in range(3):
        if i and a and b and c:
            return i
    return 0
def f_b1b_and_or_and(a, b, c, d):
    for i in range(3):
        if i:
            if not (a and b):
                if c and d:
                    return i
    return 0
def f_b1b_deep_right(a, b, c, d):
    for i in range(3):
        if i:
            if not a:
                if b and (c or d):
                    return i
    return 0
def f_b1b_not_group(a, b, c):
    for i in range(3):
        if i and not (a or b) and c:
            return i
    return 0
def f_b1b_body_before_cond(a, b, c):
    for i in range(3):
        acc = i * 2
        if a and b or c:
            return acc
    return 0
def f_b1b_import_prefix(a, b):
    import math
    for i in range(2):
        if i and (a or b):
            return math.trunc(i)
    return 0
def f_b1b_none_check_prefix(a, b):
    for i in range(3):
        s = str(i)
        if s is not None:
            if a and i:
                return s
    return 0
def f_b1b_loop_body_chain(a, b, c):
    n = 0
    while n < 3:
        if a:
            if b or c:
                n += 1
            else:
                n += 2
    return n
def f_b1b_loop_header_cond(a, b, c):
    n = 0
    while a and b or c:
        n += 1
        if n > 2:
            break
    return n
def f_b1b_ifexp_trueval(a, b, c):
    for i in range(3):
        if i:
            a and b if c else a or b
            return None
    return 0
def f_b1b_elif_mixed(a, b, c):
    for i in range(4):
        if a and b:
            return 1
        if b or c:
            return 2
        elif a or b and c:
            return 3
    return 0

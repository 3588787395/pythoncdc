# e03: B1b 五臂封闭（[B1b fix]/[B1b fix-r2] + _sb_has_body）外推 + 收缩双向变体攻击
def f_b1b_stmt_or_tail(a, b, c):
    for i in range(3):
        if i:
            if a and b or c:
                return i
    return 0


def f_b1b_shrink_or3(a, b, c):
    for i in range(3):
        if i:
            if a or b or c:
                return i
    return 0


def f_b1b_shrink_and3(a, b, c):
    for i in range(3):
        if i:
            if a and b and c:
                return i
    return 0


def f_b1b_and_or_and(a, b, c, d):
    for i in range(3):
        if i:
            if a and b or c and d:
                return i
    return 0


def f_b1b_deep_right(a, b, c, d):
    for i in range(3):
        if i:
            if a or (b and (c or d)):
                return i
    return 0


def f_b1b_not_group(a, b, c):
    for i in range(3):
        if i:
            if not (a or b) and c:
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
        if s is None or a:
            if i:
                return s
    return 0


def f_b1b_loop_body_chain(a, b, c):
    n = 0
    while n < 3:
        if a and b or c:
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
            return (a and b) if c else (a or b)
    return 0


def f_b1b_elif_mixed(a, b, c):
    for i in range(4):
        if a and b:
            return 1
        elif b or c:
            return 2
        elif a or (b and c):
            return 3
    return 0

"""负对照 1：单层三元（浅层，台账声明面内，必须 MATCH）。"""


def neg_plain_ternary_return(flag):
    return 1 if flag else 0


def neg_plain_ternary_assign(flag, x, y):
    z = x if flag else y
    return z


def neg_simple_and_or(a, b, c):
    if a and b:
        return c
    return a or b


def neg_simple_not(a):
    return not a

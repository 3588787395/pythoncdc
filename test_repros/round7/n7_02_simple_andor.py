"""负对照 2：单层 and/or + 单层三元实参（浅层，台账声明面内，必须 MATCH）。"""


def neg_or_chain(a, b, c):
    return a or b or c


def neg_and_chain(a, b, c):
    return a and b and c


def neg_ternary_arg(x, flag):
    return max(x, 1 if flag else 2)


def neg_if_and(a, b, c, d):
    if a and b or c:
        return d
    return None

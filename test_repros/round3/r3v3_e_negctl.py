"""r3v3-E 负对照——宣称已封闭形态的浅层等价物（应同时 MATCH）。"""


def n_deep_grouped_or_in_and(a, b, c):
    return (a or b) and c


def n_shallow_flat_or_and(a, b, c):
    return a or b and c


def n_deep_and_or_right(a, b, c):
    return a and (b or c)


def n_shallow_flat_and_or(a, b, c):
    return a and b or c


def n_simple_ternary(a, b, c):
    return a if b else c


def n_simple_compare(a, b):
    return a < b


def n_flat_or3(a, b, c):
    return a or b or c


def n_flat_and3(a, b, c):
    return a and b and c


def n_for_flat_return(y, a, b):
    for i in y:
        return a and b
    return 0


def n_bool_if(a, b):
    if a and b:
        return 1
    return 0

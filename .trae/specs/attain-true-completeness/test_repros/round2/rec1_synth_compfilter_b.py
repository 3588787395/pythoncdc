"""R2 合成变体 F6b（item 13 推导式元素/过滤位三元共存族，非语料）。"""


def q_elt_filter(xs, f):
    return [(x if f else 0) for x in xs if (x % 2 if f else True)]


def q_setcomp(xs, f):
    return {x if f else 1 for x in xs if (x if f else True)}


def q_genexp_elt(xs, f):
    return sum((x if f else 1 for x in xs if (x if f else True)))

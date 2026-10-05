# ne06: G6 负对照——浅层推导式（预期 MATCH）
def n_simple_listcomp(xs):
    return [x for x in xs]


def n_simple_dictcomp(xs):
    return {x: x for x in xs}


def n_simple_genexp(xs):
    return sum(x for x in xs)

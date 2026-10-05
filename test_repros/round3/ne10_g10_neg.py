# ne10: G10 负对照——浅层海象（预期 MATCH）
def n_simple_walrus(a):
    if (n := a) > 0:
        return n
    return 0


def n_walrus_while(xs):
    it = iter(xs)
    while (c := next(it, None)) is not None:
        return c
    return None

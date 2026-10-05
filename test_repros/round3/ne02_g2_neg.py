# ne02: G2 负对照——浅层三元（预期 MATCH）
def n_simple_ternary(a, b, c):
    if a:
        pass
    return b if a else c


def n_ternary_two_level(a, b, c, d):
    return a if b else (c if d else 0)

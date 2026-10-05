# ne04: G4 负对照——浅层切片/容器/星号（预期 MATCH）
def n_simple_slice(xs):
    return xs[1:3]


def n_simple_container(a, b):
    return [a, (b, 1)], {a: b}


def n_simple_star(xs):
    a, *b = xs
    return a, b

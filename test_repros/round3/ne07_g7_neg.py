# ne07: G7 负对照——浅层调用（预期 MATCH）
def n_simple_call(a, b):
    return max(a, b)


def n_simple_kwargs(a):
    def sink(x, y=1):
        return x + y
    return sink(a, y=2)


def n_simple_star(a, rest):
    def sink(x, *rs):
        return x + sum(rs)
    return sink(a, *rest)

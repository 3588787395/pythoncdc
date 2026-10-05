# ne05: G5 负对照——浅层 lambda（预期 MATCH）
def n_simple_lambda(a):
    fn = lambda x: x + 1
    return fn(a)


def n_lambda_sort(pairs):
    return sorted(pairs, key=lambda p: p[0])

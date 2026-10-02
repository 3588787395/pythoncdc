def lam_late_binding(xs):
    return [lambda: x for x in xs]


def lam_default_arg(xs):
    return [lambda x=x: x * 2 for x in xs]


def lam_with_arg(xs):
    return [lambda v, y=x: v + y for x in xs]


def lam_map_pair(xs):
    return list(map(lambda t: t[0], [(x, x * 2) for x in xs]))


def lam_call_now(xs):
    return [(lambda a: a + x)(i) for i, x in enumerate(xs)]


def lam_genexp_sort(vals):
    return sorted(((lambda: v)(), v) for v in vals)

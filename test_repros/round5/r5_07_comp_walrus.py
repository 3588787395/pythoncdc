def w_body(xs):
    out = [(y := x * 2) for x in xs]
    return out, y


def w_cond(xs):
    return [x for x in xs if (n := x * 2) > 4]


def w_body_use(xs):
    return [(m := x + 1) for x in xs]


def w_double_if(xs):
    return [x for x in xs if (p := x % 2) == 0 if (q := x // 2) > 1]


def w_two_walrus(xs):
    return [(a := x) + (b := x * 2) for x in xs]

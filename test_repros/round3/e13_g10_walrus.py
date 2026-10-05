# e13: 海象——while/if 条件、推导式条件、lambda 默认参、海象链、RHS 三元/boolop
def f_walrus_while_cond(xs):
    it = iter(xs)
    acc = []
    while (chunk := next(it, None)) is not None:
        for i in range(2):
            if i:
                acc.append(chunk)
    return acc


def f_walrus_if_cond(a):
    for i in range(3):
        if (n := len(a)) > 2:
            while i:
                return n
    return 0


def f_walrus_comp_cond(xs):
    def g(x):
        return x + 1
    for i in range(2):
        if i:
            while i:
                return [y for x in xs if (y := g(x)) > 1]
    return []


def f_walrus_lambda_default(a):
    fn = lambda x, y=(z := 2): x + y + z
    for i in range(3):
        if i:
            while i:
                return fn(a)
    return 0


def f_walrus_chain(a):
    for i in range(3):
        if i:
            while i:
                return (p := (q := (r := a) + 1) + 2) + p + q + r
    return 0


def f_walrus_rhs_ternary(a, b, c):
    for i in range(3):
        if i:
            while i:
                return (w := a if b else c) + w
    return 0


def f_walrus_rhs_boolop(a, b, c):
    for i in range(3):
        if i:
            while i:
                return (w := (a or b) and c) + w
    return 0


def f_walrus_call_arg(a):
    def sink(x):
        return x + 1
    for i in range(3):
        if i:
            while i:
                return sink((x := a)) + x
    return 0


def f_walrus_deep_host(a, b):
    try:
        for i in range(3):
            if i:
                while i:
                    if (v := a + b) > 1:
                        return v
    except ValueError:
        return -1
    return 0


def f_walrus_in_while_body(a, xs):
    n = 0
    while n < 3:
        for i in range(2):
            if (m := i + a) > 2:
                n += m
    return n


def f_walrus_elif_chain(a):
    for i in range(4):
        if (k := i * a) > 3:
            return k
        elif k > 1:
            return -k
    return 0


def f_walrus_genexp_cond(a, xs):
    for i in range(2):
        if i:
            while i:
                return sum(1 for x in xs if (y := x + a) > 1)
    return 0

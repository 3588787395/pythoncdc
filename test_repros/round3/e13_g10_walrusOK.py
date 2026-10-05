# Source Generated with Decompyle++ (Python version)
# File: e13_g10_walrus.pyc (Python 3.11)

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
        if (n := len(a)) > 2 and i:
            return n
    return 0
def f_walrus_comp_cond(xs):
    def g(x):
        return x + 1
    for i in range(2):
        if i and i:
            return [y for x in xs if (y := g(x)) > 1]
    return []
def f_walrus_lambda_default(a):
    fn = lambda x, y=(z := 2): x + y + z
    for i in range(3):
        if i and i:
            return fn(a)
    return 0
def f_walrus_chain(a):
    for i in range(3):
        if i and i:
            q = (r := a) + 1
            p = 2
            return p + q + r
    return 0
def f_walrus_rhs_ternary(a, b, c):
    for i in range(3):
        if i and i:
            (w := a if b else c) + w
    return 0
def f_walrus_rhs_boolop(a, b, c):
    for i in range(3):
        if i and i:
            (w := (c if b else w) if not a else c) + w
            return None
    return 0
def f_walrus_call_arg(a):
    def sink(x):
        return x + 1
    for i in range(3):
        if i and i:
            x = a
            return x
    return 0
def f_walrus_deep_host(a, b):
    try:
        for i in range(3):
            while i and i:
                if 1:
                    return v
    except ValueError:
        return -1
    return 0
def f_walrus_in_while_body(a, xs):
    n = 0
    while n < 3:
        for i in range(2):
            if 2:
                n += m
    return n
def f_walrus_elif_chain(a):
    for i in range(4):
        if 3:
            return k
        elif k > 1:
            return -k
        else:
            continue
    return 0
def f_walrus_genexp_cond(a, xs):
    for i in range(2):
        if i and i:
            return sum((1 for x in xs if (y := x + a) > 1))
    return 0

# e04: IfExp 三元——链式/BoolOp 分组交叉/Call 实参/返回值/推导式条件/默认参数/深宿主
def f_chain_ternary(a, b, c, d, e):
    for i in range(3):
        if i:
            while i:
                return a if b else (c if d else e)
    return 0


def f_ternary_deep_right(a, b, c, d, e, f, g):
    for i in range(3):
        if i:
            while i:
                return a if b else (c if d else (e if f else g))
    return 0


def f_ternary_boolop_group(a, b, c, d, e):
    for i in range(3):
        if i:
            while i:
                return (a or b) if c else (d and e)
    return 0


def f_ternary_call_arg(a, b, c):
    def sink(x):
        return x * 2
    for i in range(3):
        if i:
            while i:
                return sink(a if b else c)
    return 0


def f_ternary_return(a, b, c):
    for i in range(3):
        if i:
            while i:
                return a if b else c
    return 0


def f_ternary_comp_value(a, b, xs):
    for i in range(2):
        if i:
            return [x if b else -x for x in xs]
    return []


def f_ternary_comp_cond(a, b, xs):
    for i in range(2):
        if i:
            return [x for x in xs if (x if b else 0)]
    return []


def f_ternary_default_arg(a, b):
    def inner(x, y=(1 if b else 2)):
        return x + y
    for i in range(2):
        if i:
            return inner(a)
    return 0


def f_ternary_subscript(a, b, xs):
    for i in range(3):
        if i:
            while i:
                return xs[a if b else 0]
    return 0


def f_ternary_dict_value(a, b, c):
    for i in range(3):
        if i:
            while i:
                return {'k': a if b else c}
    return {}


def f_ternary_walrus_rhs(a, b, c):
    for i in range(3):
        if i:
            while i:
                return (q := a if b else c) + q
    return 0


def f_ternary_as_cond(a, b, c, xs):
    for i in range(3):
        if (a if b else c) in xs:
            while i:
                return i
    return 0


def f_ternary_nested_in_boolop(a, b, c, d):
    for i in range(3):
        if i:
            while i:
                return (a if b else c) and d
    return 0

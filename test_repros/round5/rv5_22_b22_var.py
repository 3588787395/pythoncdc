"""Round5 复核变体探针：B22（walrus 幻影目标）修复的变体攻击。"""


def q(v):
    return v + 1


def w_two_walrus_body(xs):
    """推导式体 2 个 walrus。"""
    return [(m := x * 2) + (n := x * 3) for x in xs]


def w_walrus_body_and_if(xs):
    """体 walrus + if 过滤 walrus 同推导式。"""
    return [(y := q(x)) for x in xs if (w := x)]


def w_walrus_genexp(xs):
    """GenExp 内 walrus。"""
    return any((t := x) > 3 for x in xs) and t


def w_walrus_dict(xs):
    """DictComp key/value 双 walrus。"""
    return {(k := x): (k2 := x + 1) for x in xs}

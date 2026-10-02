"""Round5 复核变体探针：B21（解包 target）修复的变体攻击。"""


def u_deep3_star(xs):
    """3 层嵌套元组 + 星号混排。"""
    return [a + b + c + d + rest[0] for (a, (b, (c, d))), *rest in xs]


def u_deep1_tuple(xs):
    """单元素元组嵌套。"""
    return [b for (a, (b,)) in xs]


def u_deep1_outer(xs):
    """单元素元组更深一层。"""
    return [b for ((b,),) in xs]


def u_star_mid(xs):
    """星号居中：a, *rest, c。"""
    return [a + b + c for a, *rest, c in xs]


def u_deep_star_mix(xs):
    """嵌套内星号：(p, (q, *r))。"""
    return [p + q + r[0] for (p, (q, *r)) in xs]

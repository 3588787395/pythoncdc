"""R7-09 链式比较基本面（同向/混合算子/非常量链）。"""


def c_two_link(a, b, c):
    return a < b < c


def c_two_link_ge(a, b, c):
    return a >= b >= c


def c_mixed_ops(a, b, c):
    return a <= b != c


def c_three_link(a, b, c, d):
    return a < b <= c < d


def c_not_in_chain(a, b, c):
    return a in b not in c


def c_is_chain(x, y, z):
    return x is y is not z

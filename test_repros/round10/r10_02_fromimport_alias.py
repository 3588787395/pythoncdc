"""r10_02: from-import 多名/括号/as 别名形态（表C relative_import 面）"""
from m1 import tool
from m2 import (alpha, beta, )
from m3 import gamma as g, delta as d


def fi_basic(k):
    if k > 0:
        return tool(k)
    return [tool(i) for i in range(k + 3)]


def fi_paren_multi(seq):
    acc = {}
    for s in seq:
        if s in acc:
            acc[s] = beta(acc[s], alpha(s))
        else:
            acc[s] = g(s)
    return acc


def fi_as_alias(flag):
    if flag:
        try:
            return d(1, 2)
        except TypeError:
            return None
    while flag is False:
        return d(0, 0)
    return None

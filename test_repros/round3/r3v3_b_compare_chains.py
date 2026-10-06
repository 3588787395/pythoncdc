"""r3v3-B 反向外推（假阴性）——位 2 _has_compare_chain_step_predecessor 前驱守卫攻击。

真·链式比较是否被误伤（含 if/while/for/三元/推导式宿主与 and/or 混排）。
"""


def cc_basic(a, b, c):
    return a < b < c


def cc_mixed(a, b, c, d):
    return a < b == c < d


def cc_in(a, b, c):
    return a in b in c


def cc_notin(a, b, c):
    return a not in b not in c


def cc_is(a, b, c):
    return a is b is not c


def cc_if(a, b, c):
    if a < b < c:
        return 1
    return 0


def cc_while(a, b, c, n):
    r = 0
    while a < b < c:
        r += 1
        if r > n:
            break
    return r


def cc_for(a, b, c, xs):
    r = 0
    for x in xs:
        if a < x < c:
            r += 1
    return r


def cc_for_value(a, b, c, xs):
    r = []
    for x in xs:
        r.append(a < x < c)
    return r


def cc_for_return(y, a, b, c):
    for i in y:
        return a < b < c
    return False


def cc_ternary(a, b, c):
    return a if a < b < c else 0


def cc_comp(a, b, c, xs):
    return [x for x in xs if a < x < c]


def cc_and(a, b, c, d):
    return a < b < c and d


def cc_or(a, b, c, d):
    return a < b < c or d

"""R2 合成变体 F9a（B123 while 头链式比较 + IfExp 尾钻石族 item 16 交叉变体，非语料）。"""


def n_chain_names(v, u, c):
    n = 0
    while 1 <= v < 9 and (u if u else v):
        v += 2
        c += 1
    return c


def n_call_else(v, w, xs):
    t = 0
    while 0 < v < 10 and (w if w else len(xs)):
        v += 1
        t += 1
    return t


def n_chain_test_var(v, w, z):
    r = 0
    while 0 < v < 10 and (w if z else v):
        v += 1
        r += 1
    return r

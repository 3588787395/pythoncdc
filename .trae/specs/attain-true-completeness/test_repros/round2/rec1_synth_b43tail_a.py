"""R2 合成变体 F8a（B43 链式比较 and 尾操作数族 item 15 交叉变体，非语料）。"""


def k_and_tail(lo, mid, hi, flag):
    return lo < mid < hi and flag


def k_store_tail(a, b, c, d):
    t = a < b < c and d
    return t


def k_if_cond(a, b, c, d):
    if a < b < c and d:
        return 1
    return 0

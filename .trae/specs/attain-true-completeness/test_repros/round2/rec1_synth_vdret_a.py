"""R2 合成变体 F4b（item 12 值菱形 Return 第三尾形族，非语料）。"""


def e_diamond_name(p, q, r, flag):
    return p if flag else q and r


def e_diamond_call(p, q, r, flag):
    return len(p) if flag else q and r


def e_diamond_binop(p, q, r, flag):
    return p + 1 if flag else q and r

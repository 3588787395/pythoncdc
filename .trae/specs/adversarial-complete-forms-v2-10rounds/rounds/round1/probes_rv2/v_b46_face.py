"""rv2 变体面 B46 尾项（r7_07 t_nest_in_condition 邻域）：条件位融合三元"""


def v_while_cond_nest(n, a, b, c, d, f1, f2):
    while (a if f1 else b) if (c if f2 else d) else 0:
        n -= 1
    return n


def v_if_cond_nest(a, b, c, d, f1, f2):
    if (a if f1 else b) if (c if f2 else d) else 0:
        return 1
    return 0


def n_for_body_nest(xs, f1, f2):
    out = []
    for x in xs:
        out.append((x if f1 else 0) if (x if f2 else 1) else 2)
    return out

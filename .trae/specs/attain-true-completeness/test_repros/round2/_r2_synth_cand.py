"""R2 synthetic replacement candidates (test batch)."""


def x1_compare_cross(p, q, r):
    return ((p or q) and r) > 2


def x2_call_in_if(p, q, r, flag):
    def sink(x):
        return x
    if flag:
        return sink((p or q) and r)
    return 0


def x3_walrus_for(p, q, r):
    for i in range(2):
        if (w := (p or q) and r):
            return w
    return -1


def x4_chain_mixed_ops(m, n, o, p, q, g1, g2):
    return (m if g1 else n) > (o if g2 else p) >= q


def x5_chain_eq_ne(m, n, o, p, q, r, g1, g2, g3):
    return (m if g1 else n) == (o if g2 else p) != (q if g3 else r)

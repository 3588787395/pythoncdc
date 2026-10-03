def chain_two_ternary(a, b, x, y, c, c1, c2):
    return (a if c1 else b) < (x if c2 else y) < c


def chain_three_ternary(a, b, x, y, m, n, c1, c2, c3):
    return (a if c1 else b) <= (x if c2 else y) < (m if c3 else n)


def chain_lhs_ternary_rhs_call(a, b, x, c1, c2):
    return (a if c1 else b) < abs(x if c2 else 0)

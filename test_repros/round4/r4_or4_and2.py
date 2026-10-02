# r4_or4_and2: B11-R2 residual probe — while (a or b or c or d) and k < m and b


def or4_and2(a, b, c, d, k, m):
    """while (a or b or c or d) and k < m and b: — or4 group with two and-tail conjuncts."""
    n = 0
    while (a or b or c or d) and k < m and b:
        n = n + 1
        k = k + 1
    return n

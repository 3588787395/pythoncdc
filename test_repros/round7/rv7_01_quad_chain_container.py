def quad_list(a, b, c, d, e, f, g, c1, c2, c3):
    return [a if c1 else b, c if c2 else d, e if c3 else f, g]


def quad_dict(k1, k2, v1, v2, v3, v4, c1, c2, c3):
    return {k1 if c1 else k2: v1 if c2 else v2, 'b': v3 if c3 else v4, 'c': v1}


def quad_tuple(a, b, x, y, m, n, c1, c2, c3):
    return (a if c1 else b, x if c2 else y, m if c3 else n, 7)

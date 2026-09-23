def w(items, a, b, c, d, out):
    for v in items:
        if a < b < c or d:
            out.append(v)
        out.append(a)
    return out

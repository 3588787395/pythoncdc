def w(items, a, b, c):
    out = []
    for v in items:
        if a < b < c:
            out.append(v)
        out.append(a)
    return out

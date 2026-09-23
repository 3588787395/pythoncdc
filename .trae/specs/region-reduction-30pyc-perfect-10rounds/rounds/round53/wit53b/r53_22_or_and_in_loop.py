def w(items, a, b, k):
    out = []
    for v in items:
        if a > b or a < k and b < k:
            out.append(v)
        else:
            out.append(k)
    return out

def w(items, a, b, k):
    out = []
    while a > b or a < k and b < k:
        a += 1
        out.append(a)
    return out

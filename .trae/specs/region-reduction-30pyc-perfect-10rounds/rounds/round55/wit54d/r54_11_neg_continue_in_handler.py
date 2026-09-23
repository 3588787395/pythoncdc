def w(g, n):
    i = 0
    acc = 0
    while i < n:
        try:
            acc += g(i)
        except Exception:
            i += 1
            continue
        i += 1
    return acc

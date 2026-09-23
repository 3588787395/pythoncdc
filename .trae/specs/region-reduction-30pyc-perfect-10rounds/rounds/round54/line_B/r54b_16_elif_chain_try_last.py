def w(xs, g, h, k, c, d):
    for x in xs:
        if c:
            a = g(x)
            continue
        elif d:
            try:
                b = h(x)
            except Exception:
                k(x)
                return b
        else:
            k(x)

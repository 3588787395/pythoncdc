def w(xs, g, h, k, c):
    for x in xs:
        if c:
            try:
                a = g(x)
            except Exception:
                h(x)
            continue
        k(x)

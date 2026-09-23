def w(xs, g, h, k, c):
    for x in xs:
        try:
            if c:
                a = g(x)
            else:
                k(x)
        except Exception:
            h(x)
            continue

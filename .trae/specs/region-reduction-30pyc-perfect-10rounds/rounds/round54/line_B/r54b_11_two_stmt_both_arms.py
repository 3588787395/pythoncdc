def w(xs, g, h, k, m, c):
    for x in xs:
        if c:
            try:
                a = g(x)
                b = h(x)
            except Exception:
                k(x)
                m(x)
                continue
        else:
            k(x)
            m(x)
            a = 0

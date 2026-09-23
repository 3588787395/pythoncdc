def w(xs, g, h, c):
    for x in xs:
        try:
            if c:
                a = g(x)
        except Exception:
            h(x)

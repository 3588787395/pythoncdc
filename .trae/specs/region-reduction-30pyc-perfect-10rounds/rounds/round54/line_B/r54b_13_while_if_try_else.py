def w(it, g, h, k, c):
    while it:
        if c:
            try:
                a = g(it)
            except Exception:
                h(it)
                continue
        else:
            k(it)

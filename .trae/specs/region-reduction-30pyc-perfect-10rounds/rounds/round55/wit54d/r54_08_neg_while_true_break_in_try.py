def w(g):
    while True:
        try:
            v = g(1)
            if v:
                break
            g(2)
        except Exception:
            g(3)
    return v

def try_finally_body(it, c, g):
    for x in it:
        try:
            g(x)
        finally:
            g(0)
        if c:
            g(1)
    g(2)

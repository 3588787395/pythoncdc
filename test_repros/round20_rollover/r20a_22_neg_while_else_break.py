def while_else_break(n, c, g):
    while n:
        n = n - 1
        if c:
            break
    else:
        g(n)
        return
    g(0)

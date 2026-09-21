def while_true_break(n, c, g):
    i = 0
    while True:
        i = i + 1
        if c:
            break
        g(i)
    g(i)

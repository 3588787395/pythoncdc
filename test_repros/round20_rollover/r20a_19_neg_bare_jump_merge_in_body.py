def merge_in_body(it, c, d, g, k):
    for x in it:
        if c:
            if d:
                g(1)
            else:
                g(2)
        else:
            g(3)
        k(x)

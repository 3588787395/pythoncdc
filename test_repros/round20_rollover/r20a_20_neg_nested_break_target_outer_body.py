def inner_break_outer_tail(it, it2, c, g):
    for x in it:
        for y in it2:
            if c:
                break
        g(x)

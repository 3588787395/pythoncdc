def arm_return(it, c, g):
    for x in it:
        if c:
            return x
        g(x)
    g(0)

# repro_03: try body with if/elif/elif/else, 4 branches all return (Pattern A2)
def f(x, a, b, c, d, e):
    try:
        if x == 1:
            return a
        elif x == 2:
            return b
        elif x == 3:
            return c
        else:
            return d
    except BaseException:
        return e

# repro_02: try body with if/elif/else, all return (Pattern A2 3-branch)
def f(x, a, b, c, d):
    try:
        if x == 1:
            return a
        elif x == 2:
            return b
        else:
            return c
    except BaseException:
        return d

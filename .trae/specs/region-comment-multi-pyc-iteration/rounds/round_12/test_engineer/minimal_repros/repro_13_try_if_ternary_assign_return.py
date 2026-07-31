# repro_13: try body if/else with ternary-assign + return (real klinedata pattern)
def f(x, a, b, c, d, e):
    try:
        if x == 1:
            a = b if c is None else d
            return a
        else:
            a = e
    except BaseException:
        return c
    return a

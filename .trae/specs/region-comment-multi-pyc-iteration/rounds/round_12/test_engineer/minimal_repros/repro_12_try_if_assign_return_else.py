# repro_12: try body if/else with assign+return in then-branch (real klinedata pattern)
def f(x, a, b, c, d):
    try:
        if x == 1:
            a = b
            return a
        else:
            c = d
    except BaseException:
        return c
    return c

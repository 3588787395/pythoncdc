# repro_07: nested if inside try, both return (Pattern A2 nested)
def f(x, a, b, c, d):
    try:
        if x == 1:
            if a:
                return b
            else:
                return c
        else:
            return d
    except BaseException:
        return a

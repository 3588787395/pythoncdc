# repro_08: if with multiple return paths in try (Pattern A2 multi-return)
def f(x, a, b, c, d):
    try:
        if x == 1:
            if a:
                return b
            return c
        else:
            return d
    except BaseException:
        return a

# repro_04: minimal 2-branch try if return else return
def f(x, a, b, c):
    try:
        if x:
            return a
        else:
            return b
    except BaseException:
        return c

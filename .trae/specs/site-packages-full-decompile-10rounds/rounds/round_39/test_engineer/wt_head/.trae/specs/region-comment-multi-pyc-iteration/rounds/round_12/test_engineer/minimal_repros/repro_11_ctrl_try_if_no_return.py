# repro_11: CONTROL — try+if but no return (should work)
def f(x, a, b, c):
    try:
        if x == 1:
            a = b
        else:
            a = c
    except BaseException:
        pass
    return a

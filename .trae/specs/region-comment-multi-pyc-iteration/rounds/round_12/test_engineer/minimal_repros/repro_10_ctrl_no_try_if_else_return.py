# repro_10: CONTROL — same but WITHOUT try (should work)
def f(x, a, b, c):
    if x == 1:
        return a
    else:
        return b

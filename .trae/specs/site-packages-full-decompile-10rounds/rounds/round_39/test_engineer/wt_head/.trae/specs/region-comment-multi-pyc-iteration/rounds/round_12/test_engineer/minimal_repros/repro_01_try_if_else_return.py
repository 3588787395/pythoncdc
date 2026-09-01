# repro_01: try body with if/else, both return (Pattern A2 minimal)
# Expected: try: if x == 1: return a / else: return b / except: return c
def f(x, a, b, c):
    try:
        if x == 1:
            return a
        else:
            return b
    except BaseException:
        return c

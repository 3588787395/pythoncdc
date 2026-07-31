# repro_06: one branch calls, other returns (Pattern A2 mixed)
def f(x, a, b, c):
    try:
        if x == 1:
            return a
        else:
            len(b)
    except BaseException:
        return c
    return b

# repro_05: one branch returns, other assigns (Pattern A2 mixed)
def f(x, a, b, c):
    try:
        if x == 1:
            return a
        else:
            b = c
    except BaseException:
        return b
    return b

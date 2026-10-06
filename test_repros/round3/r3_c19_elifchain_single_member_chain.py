def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b':
        if sv is None:
            return None
        return down(sv[-1], lv[-1])
    return None

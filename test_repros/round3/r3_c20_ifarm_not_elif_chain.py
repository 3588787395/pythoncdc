def f(t, sv, lv):
    if t == 'a':
        if sv is None or lv is None:
            return None
        return down(sv[-1], lv[-1])
    return None

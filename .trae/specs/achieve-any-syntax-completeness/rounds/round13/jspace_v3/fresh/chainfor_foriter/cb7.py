def g7(d, k, flag, n):
    d[k] = f2(d, ('w',) if flag else ())
    n = n + 1
    return n

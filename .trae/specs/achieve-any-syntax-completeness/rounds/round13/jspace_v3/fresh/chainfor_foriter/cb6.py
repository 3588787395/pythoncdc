def g6(d, k, flag):
    d[k] = f2(d, ('w',) if flag else ())
    return d[k]

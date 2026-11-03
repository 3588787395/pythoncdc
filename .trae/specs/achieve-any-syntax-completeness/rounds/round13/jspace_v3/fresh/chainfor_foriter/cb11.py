def g11(d, k, flag):
    d[k] = ('w',) if flag else ()
    for x in d:
        yield x

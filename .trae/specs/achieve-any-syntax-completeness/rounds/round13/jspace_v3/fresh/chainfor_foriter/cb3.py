def g3(d, k, flag):
    d[k] = len(d) if flag else 0
    for x in d:
        yield x

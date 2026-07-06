def test(d={}):
    for k in d:
        if d[k] > 5:
            d[k] = 0
    return d

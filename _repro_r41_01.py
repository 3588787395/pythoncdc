
def test(d, k1, k2, v, lst):
    if v < 10:
        a = d[k1] = v + 1
        d[k2] = v
        lst.append(a)
    else:
        a = 0
    return a

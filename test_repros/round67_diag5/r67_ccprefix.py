def w1(dc, s):
    k = 1
    dc = int(dc) if 0 < int(dc) <= 200 else 200
    if isinstance(s, str):
        s = [s]
    return dc, k, s
def w2(dc, s):
    if s:
        k = 1
        dc = int(dc) if 0 < int(dc) <= 200 else 200
        return dc, k
    return 0, 0
def w3(dc, s):
    if s:
        k = 1
        m = k + 2
        dc = int(dc) if 0 < int(dc) <= 200 else 200
        return dc, k, m
    return 0, 0, 0
def w4(dc, s, f):
    if s:
        f(dc)
        dc = int(dc) if 0 < int(dc) <= 200 else 200
        return dc
    return 0

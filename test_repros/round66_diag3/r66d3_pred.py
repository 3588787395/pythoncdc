def v6(dc, s):
    k = 1
    dc = int(dc) if 0 < int(dc) <= 200 else 200
    if isinstance(s, str):
        s = [s]
    return dc, k, s
def v7(dc, s):
    dc = int(dc) if 0 < int(dc) <= 200 else 200
    return dc, s

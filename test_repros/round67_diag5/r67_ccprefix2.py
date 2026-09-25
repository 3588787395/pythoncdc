def w5(dc, s):
    try:
        k = 1
        dc = int(dc) if 0 < int(dc) <= 200 else 200
    except Exception:
        dc = 0
    return dc, k
def w6(dc, s, L):
    for t in L:
        if t:
            k = 1
            dc = int(dc) if 0 < int(dc) <= 200 else 200
            s = dc if 0 < dc <= 9 else s
    return dc, k, s

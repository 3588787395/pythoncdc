def v1(dc, s):
    dc = int(dc) if dc > 0 else 200
    if isinstance(s, str):
        s = [s]
    return dc, s
def v2(dc, s):
    dc = int(dc) if 0 < int(dc) <= 200 else 200
    k = 1
    return dc, s
def v3(dc, s):
    dc = dc if 0 < dc <= 200 else 200
    if isinstance(s, str):
        s = [s]
    return dc, s
def v4(dc, s):
    dc = int(dc) if dc > 0 and dc < 300 else 200
    if isinstance(s, str):
        s = [s]
    return dc, s
def v5(dc, s):
    dc = int(dc) if 0 < int(dc) <= 200 else 200
    if s:
        s = [s]
    return dc, s

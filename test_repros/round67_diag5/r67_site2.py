def c1(dc, s):
    while dc < 50:
        k = 1
        dc = int(dc) if 0 < int(dc) <= 200 else 200
        dc += 1
    return dc, k
def c2(dc, s):
    f = lambda x: (k := 1) or (x if 0 < x <= 200 else 200)
    return f(dc)
def c3(dc, s, ctx):
    with ctx:
        k = 1
        dc = int(dc) if 0 < int(dc) <= 200 else 200
    return dc, k
def c4(dc, s):
    if s:
        k = 1
        dc = int(dc) if (dc > 0 and 0 < dc <= 200) else 200
    return dc, k
def c5(dc, s):
    try:
        k = 1
        dc = int(dc) if 0 < int(dc) <= 200 else 200
    finally:
        pass
    return dc, k
def c6(dc, s):
    if s == 1:
        k = 2
    elif s == 2:
        k = 1
        dc = int(dc) if 0 < int(dc) <= 200 else 200
    return dc, k

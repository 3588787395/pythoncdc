# Source Generated with Decompyle++ (Python version)
# File: n9v9_b104_whilehost.pyc (Python 3.11)

def w2_plain(x, n):
    r = 0
    while 0 < x < n:
        x += 1
        r += 1
    return r
def w3_plain(x, n):
    r = 0
    while 0 < x < n < 100:
        x += 1
        r += 1
        if 0 < x and n < True:
            pass
        elif n < 100:
            pass
    return r
def w3_nostore(x, n, out):
    while 0 < x < n < 100:
        x += 1
    return out
def w4_call(x, n, s):
    while 0 < x < n < len(s) < 100:
        x += 1
    return x
def w3_deep(x, n, ys):
    for y in ys:
        while 0 < y < n < 100:
            y += 1
            if 0 < y and n < True:
                continue
    return n
def w3_and(x, n, flag):
    r = 0
    while 0 < x < n and flag:
        x += 1
        r += 1
        if 0 < x < n:
            pass
    return r
def neg_for3(x, ys):
    out = []
    for y in ys:
        if 0 < y < x < 100:
            out.append(y)
    return out
def neg_ret3(a, b, c):
    return a < b < c

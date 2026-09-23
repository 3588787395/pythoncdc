def w(g, n):
    i = 0
    out = 0
    while i < n:
        i += 1
        try:
            out += g(i)
        finally:
            out += 0
        if i > 3:
            break
    return out

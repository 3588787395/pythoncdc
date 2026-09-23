def w(g, n):
    i = 0
    seen = 0
    while i < n:
        i += 1
        if g(i):
            seen = i
            break
    return seen

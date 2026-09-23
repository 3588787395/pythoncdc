def w(g, n, m):
    a = 0
    b = 0
    total = 0
    while a < n:
        a += 1
        while b < m:
            b += 1
            try:
                if g(b):
                    break
                total += 1
            except Exception:
                total -= 1
        if g(a):
            break
    return total

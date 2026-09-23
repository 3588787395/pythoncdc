def w(g, n):
    i = 0
    total = 0
    while i < n:
        i += 1
        try:
            if i > 2:
                break
            total += g(i)
        except Exception:
            total -= 1
    return total

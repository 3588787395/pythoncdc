def w(g, items):
    total = 0
    for x in items:
        try:
            total += g(x)
        except Exception:
            if x:
                break
            total -= 1
    else:
        total += 1
    return total

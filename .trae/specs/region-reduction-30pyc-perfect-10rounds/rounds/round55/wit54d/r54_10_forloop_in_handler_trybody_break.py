def w(g, items):
    total = 0
    try:
        total = g(0)
    except BaseException:
        for x in items:
            try:
                total += g(x)
                break
            except Exception as e:
                total -= 1
        if total < 0:
            return (None, 1)
    return total

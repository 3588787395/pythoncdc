def test():
    x = 0
    y = 0
    while x < 10:
        x += 1
        if x % 2 == 0:
            continue
        if x > 7:
            break
        y += 1
    return y

def test():
    x = 0
    s = 0
    while x < 10:
        x += 1
        if x < 3:
            continue
        s += x
        if x > 6:
            break
    return s

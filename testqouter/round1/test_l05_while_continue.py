def test():
    x = 0
    s = 0
    while x < 5:
        x += 1
        if x == 2:
            continue
        s += x
    return s

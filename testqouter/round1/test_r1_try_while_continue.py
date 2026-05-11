def test():
    x = 0
    y = 0
    try:
        while x < 5:
            x += 1
            if x % 2 == 0:
                continue
            y += 1
    except ValueError:
        y = -1
    return y

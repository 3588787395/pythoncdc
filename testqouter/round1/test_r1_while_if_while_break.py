def test():
    x = 0
    while x < 3:
        if x > 0:
            y = 0
            while y < 3:
                y += 1
        x += 1
    return x

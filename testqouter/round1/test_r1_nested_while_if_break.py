def test():
    x = 0
    y = 0
    while x < 3:
        while y < 3:
            y += 1
            if y > 1:
                break
        x += 1
    return x + y

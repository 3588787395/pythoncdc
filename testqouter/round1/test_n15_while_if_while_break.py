def test():
    x = 0
    while x < 5:
        if x > 0:
            y = 0
            while y < 3:
                y += 1
                if y > 2:
                    break
        x += 1
    return x + y

def test():
    x = 10
    if x > 0:
        y = 0
        while y < 5:
            y += 1
            if y > 3:
                break
    return x + y

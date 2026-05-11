def test():
    x = 0
    if True:
        while x < 5:
            x += 1
            if x > 3:
                break
    return x

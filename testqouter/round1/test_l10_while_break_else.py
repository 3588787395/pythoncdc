def test():
    x = 0
    while x < 5:
        x += 1
        if x > 2:
            break
    else:
        return 100
    return x

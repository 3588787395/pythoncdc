def test():
    x = 0
    while x < 5:
        x += 1
        if x > 10:
            break
    else:
        x = 100
    return x

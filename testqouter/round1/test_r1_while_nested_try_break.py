def test():
    x = 0
    while x < 10:
        try:
            x += 1
            if x > 5:
                break
        except ValueError:
            x = 0
    return x

def test():
    x = 0
    while x < 3:
        try:
            x += 1
        except ValueError:
            x = 0
    return x

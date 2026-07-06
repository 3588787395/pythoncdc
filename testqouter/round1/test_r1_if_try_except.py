def test():
    x = 10
    if x > 0:
        try:
            x += 1
        except ValueError:
            x = 0
    return x

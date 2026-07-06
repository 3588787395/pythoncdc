def test():
    a, b = 5, 10
    x = a if a > b else b
    y = b if b > a else a
    return x, y

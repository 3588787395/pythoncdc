def test():
    f = lambda x: x > 0 and x < 10 or x == -1
    return [f(i) for i in [5, -1, 15]]

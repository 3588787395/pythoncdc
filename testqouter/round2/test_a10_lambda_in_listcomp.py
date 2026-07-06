def test():
    data = [(1, 2), (3, 4)]
    return [((lambda p: p[0] + p[1])(x)) for x in data]

def test():
    data = [1, 2, 3, 4]
    result = list(map(lambda x: x * 2, data))
    return sum(result)

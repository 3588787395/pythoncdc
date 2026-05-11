def test():
    result = []
    for i in range(3):
        try:
            x = 10 // (i + 1)
            result.append(x)
        except ZeroDivisionError:
            result.append(-1)
    return result

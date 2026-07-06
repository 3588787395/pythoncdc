def test():
    result = []
    x = 0
    while x < 3:
        try:
            y = 10 // (x + 1)
            result.append(y)
        except ZeroDivisionError:
            result.append(-1)
        x += 1
    return result

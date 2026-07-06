def test():
    result = 0
    for i in range(10):
        try:
            if i > 3:
                break
            result += i
        except ValueError:
            result = 0
    return result

def test():
    result = 0
    for i in range(5):
        try:
            result += i
        except ValueError:
            result -= 1
    return result

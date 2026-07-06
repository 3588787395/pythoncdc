def test():
    result = 0
    try:
        for i in range(10):
            if i > 3:
                break
            result += i
    except ValueError:
        result = -1
    return result

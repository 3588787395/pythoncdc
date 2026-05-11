def test():
    result = 0
    for i in range(5):
        if i > 2:
            try:
                result += i
            except ValueError:
                result = 0
    return result

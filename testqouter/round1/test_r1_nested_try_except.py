def test():
    result = 0
    try:
        try:
            x = 1 / 0
        except ZeroDivisionError:
            result = 1
    except:
        result = 2
    return result

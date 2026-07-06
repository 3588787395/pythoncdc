def test():
    try:
        try:
            x = 1 / 0
        except ZeroDivisionError:
            return 1
    except:
        return 2
    return 0

def test():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        return 1
    return 0

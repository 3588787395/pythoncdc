def test():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        x = 0
    finally:
        y = 1
    return x

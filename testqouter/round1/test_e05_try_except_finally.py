def test():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        x = -1
    finally:
        x = x * 2 if 'x' in dir() else 0
    return x

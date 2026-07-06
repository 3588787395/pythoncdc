def test():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        x = 0
        if x < 0:
            raise ValueError('neg')
    return x

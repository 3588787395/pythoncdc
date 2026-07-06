def test():
    try:
        x = int('a')
    except ValueError as e:
        x = 0
    except TypeError:
        x = -1
    return x

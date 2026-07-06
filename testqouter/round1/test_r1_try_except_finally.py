def test():
    try:
        x = 1
    except ValueError:
        x = -1
    finally:
        x = x * 2
    return x

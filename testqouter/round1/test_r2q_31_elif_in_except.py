def test():
    try:
        x = 1
    except ValueError as e:
        if x > 0:
            x = 2
        elif x < 0:
            x = -2
        else:
            x = 0
    return x

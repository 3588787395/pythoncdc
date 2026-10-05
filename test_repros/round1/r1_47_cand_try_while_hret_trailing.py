def f47(x):
    try:
        while x < 3:
            x += 1
    except BaseException:
        print('e')
        return None
    return None

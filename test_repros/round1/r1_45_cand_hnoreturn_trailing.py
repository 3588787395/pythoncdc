def f45(x):
    try:
        if x == 1:
            print('a')
        else:
            print('b')
    except BaseException:
        print('e')
    return None

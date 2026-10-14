def f49(x):
    try:
        try:
            if x == 1:
                print('a')
            else:
                print('b')
        except ValueError:
            print('inner')
    except BaseException:
        print('e')
        return None
    return None

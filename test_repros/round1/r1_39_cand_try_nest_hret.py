def f39(x):
    try:
        if x == 1:
            if x == 2:
                print('a')
            else:
                print('b')
            print('c')
        else:
            print('d')
    except BaseException:
        print('e')
        return None

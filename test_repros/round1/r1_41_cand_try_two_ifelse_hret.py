def f41(x):
    try:
        if x == 1:
            print('a')
        else:
            print('b')
        if x == 2:
            print('c')
        else:
            print('d')
    except BaseException:
        print('e')
        return None

def f44(x):
    try:
        if x is None:
            print('g')
            return None
        if x == 1:
            if x == 2:
                print('i')
            else:
                print('o')
            print('t')
        else:
            print('b')
        if x == 3:
            print('c')
        else:
            print('d')
    except BaseException:
        print('e')
        return None
    return None

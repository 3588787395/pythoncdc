def f37(x):
    try:
        if x == 1:
            print('a')
        elif x == 2:
            print('b')
        else:
            print('c')
    except BaseException as exc:
        print(exc)

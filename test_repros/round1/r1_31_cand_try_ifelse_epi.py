def f31(x):
    try:
        if x == 1:
            print('a')
        else:
            print('b')
    except BaseException as exc:
        print(exc)

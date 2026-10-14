def f33(x):
    try:
        if x == 1:
            print('a')
        else:
            print('b')
        print('after')
    except BaseException as exc:
        print(exc)

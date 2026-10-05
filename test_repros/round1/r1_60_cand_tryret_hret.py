def f60(x):
    try:
        if x:
            print('a')
        return x
    except BaseException:
        print('e')
        return x

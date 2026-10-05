def f48(x):
    try:
        for i in x:
            print(i)
    except BaseException:
        print('e')
        return None
    return None

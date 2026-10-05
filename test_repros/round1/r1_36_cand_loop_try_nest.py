def f36(xs):
    try:
        for x in xs:
            if x == 1:
                if x == 2:
                    print('a')
                else:
                    print('b')
                print('c')
            else:
                print('d')
    except BaseException as exc:
        print(exc)

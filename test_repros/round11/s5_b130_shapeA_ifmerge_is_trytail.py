def f5(cond):
    a = 0
    try:
        if cond:
            a = 1
            print(a)
        else:
            print('err')
        print('tail')
    except Exception as e:
        print(e)
    finally:
        print('fin')
    return a

def f9(cond, x, tail=0):
    try:
        if cond:
            if x == 0:
                raise ValueError('zero')
            tail = 1
            print('then')
        else:
            print('err')
        print('tail')
    except Exception as e:
        print(e)
    finally:
        print('fin')
    return tail

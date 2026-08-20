def risky(x):
    try:
        1 / x
    except ZeroDivisionError:
        print('done')
        return 0
    else:
        return print('done')
    finally:
        print('done')

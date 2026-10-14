def f72(r):
    while r:
        try:
            print('get')
        except ValueError:
            print('empty')
        else:
            print('ok')
    return None

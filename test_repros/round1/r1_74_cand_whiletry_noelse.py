def f74(r, v):
    if v == 3:
        while r:
            try:
                print('get')
            except ValueError:
                print('empty')
        return None
    if v == 5:
        print('five')
    return None

def f73(r, v):
    if v == 3:
        for _ in r:
            try:
                print('get')
            except ValueError:
                print('empty')
            else:
                print('ok')
        return None
    if v == 5:
        print('five')
    return None

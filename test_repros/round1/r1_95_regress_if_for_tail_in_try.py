def f95(x, items, store):
    try:
        if x:
            for k in items:
                store.pop(k)
    except BaseException:
        print('e')
        return None
    return None

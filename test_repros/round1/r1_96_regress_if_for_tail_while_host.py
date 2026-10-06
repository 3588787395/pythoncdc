def f96(n, items, store):
    while n > 0:
        n -= 1
        if n:
            for k in items:
                store.pop(k)
    if n:
        for k in items:
            store.append(k)

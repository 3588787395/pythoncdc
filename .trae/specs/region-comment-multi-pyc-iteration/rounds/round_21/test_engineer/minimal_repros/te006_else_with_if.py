def f(items):
    for item in items:
        try:
            x = read(item)
        except IOError:
            continue
        else:
            if x is not None:
                save(x)

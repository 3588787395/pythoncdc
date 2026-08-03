def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            continue
        else:
            save(x)

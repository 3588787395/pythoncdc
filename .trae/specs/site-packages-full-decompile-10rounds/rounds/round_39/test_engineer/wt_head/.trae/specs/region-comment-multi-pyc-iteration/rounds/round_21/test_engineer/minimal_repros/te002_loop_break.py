def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            break
        else:
            save(x)

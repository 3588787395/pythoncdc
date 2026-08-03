def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            return None
        else:
            save(x)

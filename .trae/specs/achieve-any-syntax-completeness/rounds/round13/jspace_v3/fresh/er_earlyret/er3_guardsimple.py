def f(items):
    while True:
        if not items:
            return None
        items = items[1:]
        print(items)

def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            continue
        else:
            if x > 0:
                save(x)
            else:
                discard(x)

def f(items):
    for item in items:
        try:
            x = process(item)
        except ValueError:
            log("error")
            continue
        else:
            save(x)

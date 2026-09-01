def f(items):
    for item in items:
        try:
            data = read(item)
        except IOError:
            continue
        else:
            for d in data:
                write(d)

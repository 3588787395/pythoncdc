def f(data):
    for d in data:
        try:
            x = parse(d)
        except ValueError:
            continue
        else:
            try:
                y = transform(x)
            except KeyError:
                continue
            else:
                save(y)

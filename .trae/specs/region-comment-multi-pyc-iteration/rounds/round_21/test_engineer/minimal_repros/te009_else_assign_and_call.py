def f(items):
    for item in items:
        try:
            result = compute(item)
        except ValueError:
            continue
        else:
            msg = format(result)
            send(msg)

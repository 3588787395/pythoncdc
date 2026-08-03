def f():
    while running():
        try:
            data = read_stream()
        except IOError:
            continue
        else:
            process(data)

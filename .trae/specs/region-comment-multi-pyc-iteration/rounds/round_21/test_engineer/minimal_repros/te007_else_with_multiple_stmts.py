def f(items):
    for item in items:
        try:
            buf = get_buf(item)
            text = buf.read()
        except IOError:
            continue
        else:
            msg = encode(text)
            write(msg)
            flush()

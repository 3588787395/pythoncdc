def f(items):
    for item in items:
        try:
            x = process(item)
        except (IOError, EOFError):
            continue
        except ValueError:
            continue
        else:
            save(x)

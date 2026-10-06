def n_except_star(fn):
    r = None
    try:
        fn()
    except* ValueError as eg:
        r = eg.exceptions
    return r


def n_except_star_two(fn):
    try:
        fn()
    except* ValueError as eg:
        handle(eg)
    except* TypeError as eg:
        handle(eg)
    return None

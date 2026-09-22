STORE = {}


def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            break
    return tc in STORE

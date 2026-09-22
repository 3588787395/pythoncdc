STORE = {}


def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            tc = tc[:i]
    return tc in STORE

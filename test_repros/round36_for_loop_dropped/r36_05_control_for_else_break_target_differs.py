STORE = {}


def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            tc = tc[:i]
            break
    else:
        tc = 'x'
    return tc in STORE

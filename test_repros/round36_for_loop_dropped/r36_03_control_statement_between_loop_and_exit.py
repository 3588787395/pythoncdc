STORE = {}


def f(tc):
    for i, c in enumerate(tc):
        if c.isdigit():
            tc = tc[:i]
            break
    tc = tc.strip()
    return tc in STORE

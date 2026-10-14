# round-2 r2v3 specimen (synthetic, minimal)
def f(a, b, c):
    try:
        if a is None or b is None:
            return c
        use(a)
    except ValueError:
        log('e')
    return c

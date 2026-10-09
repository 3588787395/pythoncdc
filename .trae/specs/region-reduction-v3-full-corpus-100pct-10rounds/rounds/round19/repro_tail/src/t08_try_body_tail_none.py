def f(a):
    try:
        if a:
            return
    except ValueError:
        return
    return None, a

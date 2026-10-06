def f(a):
    try:
        while a > 0:
            a -= 1
    finally:
        pass
    return a

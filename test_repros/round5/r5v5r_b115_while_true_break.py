def f(a):
    while a and a > 0:
        a -= 1
        if a < 0:
            break
    return a

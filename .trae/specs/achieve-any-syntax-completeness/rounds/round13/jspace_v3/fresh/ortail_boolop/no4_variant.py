def f(a, b, c, n):
    if n == 1:
        return 0
    elif a and (b or c):
        return 1
    return 2

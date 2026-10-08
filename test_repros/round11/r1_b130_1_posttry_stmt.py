def f(x):
    try:
        y = int(x)
    except ValueError:
        y = 0
    print(y)
    return y

def g(x):
    try:
        y = int(x)
    except ValueError:
        y = 0
    else:
        y = y + 1
    print(y)
    return y

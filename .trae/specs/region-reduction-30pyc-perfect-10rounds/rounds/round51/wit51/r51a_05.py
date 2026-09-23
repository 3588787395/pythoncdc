
def f(a, b):
    if b:
        if a == 1:
            a += 1
        elif a == 2:
            a += 2
    else:
        if a == 3:
            a += 3
        elif a == 4:
            a += 4
        else:
            pass
    return a

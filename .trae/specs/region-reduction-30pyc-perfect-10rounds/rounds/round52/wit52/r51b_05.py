
def f(a, b):
    try:
        if b:
            if a == 1:
                a += 1
            elif a == 2:
                a += 2
            else:
                pass
        elif a == 3:
            a += 3
    except ValueError:
        a = 0
    return a

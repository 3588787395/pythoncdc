def f(a, b):
    if a == 1:
        if b == 'x':
            x = 1
        else:
            x = 2
    else:
        if b == 'y':
            y = [1]
        elif b == 'z':
            y = [2]
        else:
            y = [3]
        for i in y:
            z = i
    return z

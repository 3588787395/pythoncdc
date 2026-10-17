
def f(a, b, c, d):
    for i in range(3):
        if i:
            while i < 4:
                return ((a or b) and c) if d else 0
    return 1


def test():
    s = 0
    for i in range(3):
        try:
            s += 10 // (i + 1)
        except ZeroDivisionError:
            s -= 1
    return s

def test():
    x = 0
    s = 0
    while x < 3:
        for i in range(2):
            s += i
        x += 1
    return s

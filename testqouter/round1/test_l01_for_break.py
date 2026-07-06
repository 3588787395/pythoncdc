def test():
    s = 0
    for i in range(10):
        s += i
        if s > 10:
            break
    return s

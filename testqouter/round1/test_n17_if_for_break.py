def test():
    s = 0
    if True:
        for i in range(5):
            s += i
            if s > 3:
                break
    return s

def test():
    s = 0
    for i in range(10):
        if i < 3:
            continue
        s += i
        if i > 6:
            break
    return s

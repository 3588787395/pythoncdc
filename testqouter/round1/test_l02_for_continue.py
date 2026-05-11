def test():
    s = 0
    for i in range(5):
        if i == 2:
            continue
        s += i
    return s

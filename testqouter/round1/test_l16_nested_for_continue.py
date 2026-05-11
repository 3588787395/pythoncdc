def test():
    s = 0
    for i in range(3):
        for j in range(5):
            if j == 2:
                continue
            s += j
    return s

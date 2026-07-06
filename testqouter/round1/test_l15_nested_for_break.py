def test():
    s = 0
    for i in range(5):
        for j in range(5):
            s += j
            if s > 10:
                break
    return s

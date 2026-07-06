def test():
    s = 0
    for i in range(3):
        j = 0
        while j < 2:
            s += j
            j += 1
    return s

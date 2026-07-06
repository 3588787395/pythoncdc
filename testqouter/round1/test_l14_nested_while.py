def test():
    i = 0
    s = 0
    while i < 3:
        j = 0
        while j < 3:
            s += j
            j += 1
        i += 1
    return s

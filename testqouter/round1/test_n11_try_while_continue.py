def test():
    x = 0
    try:
        while x < 10:
            if x < 3:
                x += 1
                continue
            x += 2
    except:
        return -1
    return x

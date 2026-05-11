def test():
    s = 0
    try:
        for i in range(3):
            s += i
    except:
        return -1
    return s

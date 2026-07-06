def test():
    try:
        for i in range(10):
            if i > 5:
                break
    except:
        return -1
    return i

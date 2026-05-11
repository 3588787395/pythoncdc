def test():
    for i in range(10):
        if i == 5:
            break
        if i == 3:
            continue
    return i

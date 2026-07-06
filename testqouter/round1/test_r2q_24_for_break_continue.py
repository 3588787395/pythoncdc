def test():
    for i in range(3):
        if i == 1:
            continue
        if i == 2:
            break
    return i

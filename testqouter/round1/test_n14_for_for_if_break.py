def test():
    for i in range(3):
        for j in range(3):
            if j > i:
                break
    return i + j

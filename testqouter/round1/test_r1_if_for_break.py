def test():
    x = 10
    if x > 0:
        for i in range(5):
            if i > 2:
                break
            x += i
    return x

def test():
    counter = [0]
    f = lambda: counter.__setitem__(0, counter[0] + 1) or counter[0]
    f(); f()
    return counter[0]

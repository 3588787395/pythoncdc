def test():
    f = lambda x: 'positive' if x > 0 else ('zero' if x == 0 else 'negative')
    return f(5), f(0), f(-3)

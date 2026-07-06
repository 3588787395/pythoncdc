def test():
    def make_adder(n):
        return lambda x: x + n
    add5 = make_adder(5)
    return add5(10)

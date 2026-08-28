def f(self, x):
    y = self.compute(x)
    assert y is not None
    self.result = y

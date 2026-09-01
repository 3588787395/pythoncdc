def f(self, trade):
    amount = trade.amount
    assert self.a + amount <= self.b, 'over'
    return amount

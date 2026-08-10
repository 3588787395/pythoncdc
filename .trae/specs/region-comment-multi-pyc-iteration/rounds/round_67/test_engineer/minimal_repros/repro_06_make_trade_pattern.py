
def make_trade(self, trade):
    amount = trade
    if trade > 0:
        if trade == 1:
            if self.count == 0:
                self.time = trade
            self.type = 1
            self.price = (self.price * self.count + amount * trade) / (self.count + amount)
            self.cost += trade
            self.list.insert(0, (trade, amount))
            return -1 * self.calc(amount, trade)
        else:
            if self.count - amount != 0:
                self.price = (self.price * self.count - amount * trade) / (self.count - amount)
            else:
                self.time = trade
                self.price = 0.0
            old = self.margin
            self.cost += trade
            delta = self.close(trade)
            self.pnl += delta
            return old - self.margin + delta
    return 0

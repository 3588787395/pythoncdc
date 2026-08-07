class Foo:
    def make_trade(self, trade):
        amount = trade.amount
        if trade.direction == 1:
            if trade.sub == 0:
                if self.count == 0:
                    self.time = trade.date
                self.type = 1
                self.avg = (self.avg * self.count + amount * trade.price) / (self.count + amount)
                self.cost += trade.cost
                self.list.insert(0, (trade.price, amount))
                return -1
            else:
                if self.count - amount != 0:
                    self.avg = (self.avg * self.count - amount * trade.price) / (self.count - amount)
                else:
                    old = self.val
                    self.cost += trade.cost
                    delta = self.close(trade)
                    self.pnl += delta
                    return old - self.val + delta
        else:
            if trade.sub == 0:
                if self.count2 == 0:
                    self.time2 = trade.date
                self.type = 2
                self.avg2 = (self.avg2 * self.count2 + amount * trade.price) / (self.count2 + amount)
                self.cost2 += trade.cost
                self.list2.insert(0, (trade.price, amount))
                return -1
            else:
                if self.count2 - amount != 0:
                    self.avg2 = (self.avg2 * self.count2 - amount * trade.price) / (self.count2 - amount)
                else:
                    self.time2 = trade.date
                    self.avg2 = 0.0
                old = self.val
                self.cost2 += trade.cost
                delta = self.close(trade)
                self.pnl2 += delta
                return old - self.val + delta


def close_holding_repro(self, trade):
    left_amount = trade
    delta = 0
    if trade > 0:
        if trade == 1:
            left_amount = trade
            while left_amount > 0 and self.data:
                item = self.data.pop()
                if item > left_amount:
                    consumed = left_amount
                else:
                    consumed = item
                left_amount -= consumed
                delta += item
        else:
            if self.old_data:
                old = self.old_data.pop()
                if old > left_amount:
                    return old
                else:
                    left_amount -= old
                    delta += old
                    while left_amount > 0 and self.data:
                        item = self.data.pop()
                        left_amount -= item
                    return delta
    return delta

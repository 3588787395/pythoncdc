# Source Generated with Decompyle++ (Python version)
# File: c02_genexpr_and_predicate.pyc (Python 3.11)

class P:
    def buy_open_order_amount(self):
        return sum((o.unfilled_amount for o in self.open_orders if o.entrust_direction == EntrustDirection.BUY and o.futures_direction == FuturesDirection.OPEN))
    def sell_open_order_amount(self):
        return sum((o.unfilled_amount for o in self.open_orders if o.entrust_direction == EntrustDirection.SELL and o.futures_direction == FuturesDirection.CLOSE))

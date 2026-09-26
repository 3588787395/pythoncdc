# Source Generated with Decompyle++ (Python version)
# File: b02_genexpr_pred_jump.pyc (Python 3.11)

class P:
    def buy_open_order_amount(self):
        amount = sum((o.amount for o in self._orders if o.side == BUY))
        return amount
    def sell_open_order_amount(self):
        amount = sum((o.amount for o in self._orders if o.side == SELL))
        return amount
    def close_today_amount(self):
        return sum((o.amount for o in self._orders if o.offset == CLOSE_TODAY))

"""R102-06 rich: subscript augassign in for+if/elif/else with attribute augassign sibling.

stock_account.update_account 同型富上下文:
双 for 循环 + if/elif/else + continue, 属性增广赋值与下标增广赋值相邻。
"""


class BUY:
    pass


class six:
    @staticmethod
    def iteritems(d):
        return d.items()


class SA:
    def _make_trade(self, trade):
        self.last = trade

    def update_account(self, orders, trades=list()):
        for trade in trades:
            if trade.id in self._processed_trade:
                continue
            self._make_trade(trade)
        self._frozen_cash = 0
        frozen_amount = {}
        for order in orders:
            if order.is_final():
                continue
            elif order.entrust_direction == BUY:
                self._frozen_cash += order.frozen_price * order.unfilled_amount
                continue
            else:
                frozen_amount[order.symbol] += order.unfilled_amount
        for symbol, position in six.iteritems(self._positions):
            position.reset_frozen(frozen_amount[symbol])

class A:
    def __init__(self, total_cash, positions, processed_trade=None):
        self._total_cash = total_cash
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._transaction_cost = 0
        self.register_event()

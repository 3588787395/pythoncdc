class A:
    def __init__(self, processed_trade=None):
        self._a = 1
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._b = 0
        self.register_event()

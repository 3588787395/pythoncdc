class A:
    def __init__(self, processed_trade=None):
        self._processed_trade = processed_trade if processed_trade is not None else set()

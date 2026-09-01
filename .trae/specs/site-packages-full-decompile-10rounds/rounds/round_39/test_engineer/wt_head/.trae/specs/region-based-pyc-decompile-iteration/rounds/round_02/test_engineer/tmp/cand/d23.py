def last_price(self, np, Engine):
    if not np.isnan(self._last_price):
        return self._last_price
    last_price = Engine.instance().get_last_price(self.symbol)
    if np.isnan(last_price):
        raise RuntimeError('nan'.format(self.symbol))
    return last_price

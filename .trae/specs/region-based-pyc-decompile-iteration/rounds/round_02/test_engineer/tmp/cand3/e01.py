def __missing__(self, symbol):
    symbol = endswith_transe_2to4(symbol)
    r = self.get(symbol, None)
    if r is not None:
        return r
    symbol = symbol.replace('XSHG', 'SS').replace('XSHE', 'SZ')
    r = self.get(symbol, None)
    if r is not None:
        return r
    try:
        return Position(self._engine.portfolio.positions[symbol])
    except (AttributeError, KeyError):
        raise KeyError(symbol)

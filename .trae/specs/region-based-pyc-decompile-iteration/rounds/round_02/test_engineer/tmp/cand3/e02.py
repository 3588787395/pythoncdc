def f(self, symbol):
    try:
        return Position(self._engine.portfolio.positions[symbol])
    except (AttributeError, KeyError):
        raise KeyError(symbol)

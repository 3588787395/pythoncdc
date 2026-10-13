# Source Generated with Decompyle++ (Python version)
# File: r8v8fb_finreg.pyc (Python 3.11)

items = {'kA1': 1, 'kC2': 2}
d = {k.replace('a', 'b').replace('c', 'd'): v for k, v in items.items()}
class Position:
    def __init__(self, engine, position):
        self.engine = engine
        self.position = position
class PositionDict(dict):
    def __init__(self, positions):
        self._positions = positions
        super().__init__({symbol.replace('XSHE', 'SZ').replace('XSHG', 'SS'): Position(self, position) for symbol, position in positions.items()})
d2 = {k.replace('a', 'b'): v for k, v in items.items()}
d3 = {k: v.replace('a', 'b').replace('c', 'd') for k, v in items.items()}

# [Round8 回退整改 P0] finance.pyc PositionDict.__init__.<dictcomp> 键链蒸发最小复现
# 回退事实：6c4468ef 整改批引入——dictcomp 键 = 循环变量上的方法链 Call
# （k.replace('a','b').replace('c','d')）整体蒸发，键只剩裸循环变量。
# 形 A：模块级裸 dictcomp（键链同形）
items = {'kA1': 1, 'kC2': 2}
d = {k.replace('a', 'b').replace('c', 'd'): v for k, v in items.items()}

# 形 B：PositionDict 原形（类方法内 super().__init__ 宿主 + 闭包 deref）
class Position:
    def __init__(self, engine, position):
        self.engine = engine
        self.position = position

class PositionDict(dict):
    def __init__(self, positions):
        self._positions = positions
        super().__init__({symbol.replace('XSHE', 'SZ').replace('XSHG', 'SS'): Position(self, position) for symbol, position in positions.items()})

# 形 C：非链单方法键（对照——验证链长敏感性）
d2 = {k.replace('a', 'b'): v for k, v in items.items()}

# 形 D：值侧方法链（对照——键/值位置敏感性）
d3 = {k: v.replace('a', 'b').replace('c', 'd') for k, v in items.items()}

# Source Generated with Decompyle++ (Python version)
# File: r1_91_regress_if_for_tail_stock.pyc (Python 3.11)

def f91(self, data, positions, cash):
    if data:
        for symbol, value in data.items():
            position = positions[symbol]
            position.allotted(int(value * cash))
            if value < self.cash:
                position.rationed(int(value), cash)
                self.total_cash -= value

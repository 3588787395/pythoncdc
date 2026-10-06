def f91(self, data, positions, cash):
    if data:
        for symbol, value in data.items():
            position = positions[symbol]
            position.allotted(int(value * cash))
            if value < self.cash:
                position.rationed(int(value), cash)
                self.total_cash -= value

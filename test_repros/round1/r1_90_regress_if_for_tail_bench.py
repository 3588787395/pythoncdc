def f90(self, mergered_data, positions):
    if mergered_data:
        for symbol, mergered in mergered_data.items():
            old = positions.get(symbol)
            positions.pop(symbol)
            print(old, mergered)

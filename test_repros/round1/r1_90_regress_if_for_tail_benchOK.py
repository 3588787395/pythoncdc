# Source Generated with Decompyle++ (Python version)
# File: r1_90_regress_if_for_tail_bench.pyc (Python 3.11)

def f90(self, mergered_data, positions):
    if mergered_data:
        for symbol, mergered in mergered_data.items():
            old = positions.get(symbol)
            positions.pop(symbol)
            print(old, mergered)

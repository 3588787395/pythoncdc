# Source Generated with Decompyle++ (Python version)
# File: repro_04_float_div_in_call.pyc (Python 3.11)

def close_percent(price5, price10, price):
    p1 = float(price5 / price)
    p2 = float(price10 / price)
    return p1 + p2

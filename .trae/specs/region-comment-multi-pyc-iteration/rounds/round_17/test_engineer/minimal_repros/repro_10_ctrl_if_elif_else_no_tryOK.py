# Source Generated with Decompyle++ (Python version)
# File: repro_10_ctrl_if_elif_else_no_try.pyc (Python 3.11)

def classify(x, amt):
    if x == 'a':
        amt = int(amt / 10) * 10
    elif x == 'b':
        amt = int(amt / 100) * 100
    else:
        amt = int(amt)
    return amt

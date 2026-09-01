# Source Generated with Decompyle++ (Python version)
# File: repro_09_if_elif_else_slice_in_tuple.pyc (Python 3.11)

def amount_trans(stock, amount):
    if stock[:2] == '68':
        if amount < 200:
            return 0
        else:
            return int(amount)
    elif stock[:2] in ('11', '10', '12'):
        amount = int(amount / 10) * 10
    else:
        amount = int(amount / 100) * 100
    return amount

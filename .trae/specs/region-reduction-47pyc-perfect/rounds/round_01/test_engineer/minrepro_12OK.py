# Source Generated with Decompyle++ (Python version)
# File: minrepro_12.pyc (Python 3.11)

def elif_chain_with_or(x, y):
    if x == 1:
        return 'a'
    elif x == 2 or y == 3:
        return 'b'
    elif x == 3 and y == 4:
        return 'c'
    else:
        return 'd'

# Source Generated with Decompyle++ (Python version)
# File: r6_b117_a03_forelse_ctl.pyc (Python 3.11)

def r6_b117_a03_forelse_ctl(items):
    for x in items:
        if x > 3:
            break
    else:
        total = 0
        for y in items:
            total += y
        if total > 2:
            total = 0
    return 1

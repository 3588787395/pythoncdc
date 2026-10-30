# Source Generated with Decompyle++ (Python version)
# File: m5.pyc (Python 3.11)

def m5(bases):
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    items = list(bases)
    return (boundary, items)

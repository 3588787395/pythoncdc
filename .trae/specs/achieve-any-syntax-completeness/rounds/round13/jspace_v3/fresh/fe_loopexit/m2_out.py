# Source Generated with Decompyle++ (Python version)
# File: m2.pyc (Python 3.11)

def m2(bases):
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    else:
        boundary = 0
    items = list(bases)
    return (boundary, items)

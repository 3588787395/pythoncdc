# Source Generated with Decompyle++ (Python version)
# File: m4.pyc (Python 3.11)

def m4(bases):
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    else:
        boundary = 0
    items = boundary
    return (boundary, items)

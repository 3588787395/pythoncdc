# Source Generated with Decompyle++ (Python version)
# File: m3.pyc (Python 3.11)

def m3(bases):
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    else:
        boundary = 0
    if bases:
        return list(bases)
    else:
        return []
    items = list(bases) if bases else []
    return (boundary, items)

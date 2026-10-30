# Source Generated with Decompyle++ (Python version)
# File: fe1_repro.pyc (Python 3.11)

def m(bases, abcs=None):
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
        items = list(abcs) if abcs else []
        extra = boundary + 1
        return (boundary, items, extra)
    else:
        boundary = 0

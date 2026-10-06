# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2a02.pyc (Python 3.11)

def b2a02_shallow(items, limit):
    out = []
    for it in items:
        if it > limit:
            continue
        out.append(it)
        continue
    return out
def b2a02_deep(items, limit):
    out = []
    while limit > 0:
        try:
            for it in items:
                if it > 0:
                    if it > limit:
                        continue
                    out.append(it)
        except ValueError:
            limit = 0
        limit -= 1
    return out

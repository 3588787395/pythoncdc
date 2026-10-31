# Source Generated with Decompyle++ (Python version)
# File: pc6.pbpyc (Python 3.11)

def f(items):
    out = 0
    i = 0
    while i < len(items):
        d = items[i]
        if d is None:
            continue
        if d > 2:
            out += d
            break
        i += 1
    return out

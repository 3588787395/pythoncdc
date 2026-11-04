# Source Generated with Decompyle++ (Python version)
# File: pe8.pyc (Python 3.11)

def f(items):
    out = 0
    i = 0
    while 1:
        if i < len(items):
            d = items[i]
            if d is not None:
                out += d
                i += 1
                continue
        else:
            return out

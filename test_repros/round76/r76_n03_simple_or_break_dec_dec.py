# Source Generated with Decompyle++ (Python version)
# File: r76_n03_simple_or_break_dec.pyc (Python 3.11)

def f(data, series):
    out = []
    for n in series:
        if data[n] is not None:
            if data[n] < 0:
                break
            out.append(data[n])
            continue
    return out
